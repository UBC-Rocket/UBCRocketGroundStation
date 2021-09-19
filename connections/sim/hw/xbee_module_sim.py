from enum import IntEnum
from queue import SimpleQueue
from threading import Thread, RLock

from util.detail import LOGGER
from util.event_stats import Event

START_DELIMITER = 0x7E
ESCAPE_CHAR = 0x7D
ESCAPE_XOR = 0x20
XON = 0x11
XOFF = 0x13
NEEDS_ESCAPING = (START_DELIMITER, ESCAPE_CHAR, XON, XOFF)
XBEE_BROADCAST_ADDRESS = bytes.fromhex("000000000000FFFF")

FRAME_PARSED_EVENT = Event("frame_parsed")
SENT_TO_ROCKET_EVENT = Event("sent_to_rocket")


class FrameType(IntEnum):
    TX_REQUEST = 0x10
    TX_STATUS = 0x8B
    RX_INDICATOR = 0x90


class UnescapedDelimiterError(Exception):
    """
    Raises if there's an unescaped start delimiter.
    As per the XBee spec, this is eventually handled by discarding the packet so far and rebuilding.
    """


class ChecksumMismatchError(Exception):
    """
    Raised when the calculated checksum does not match the sent checksum
    """


class ShuttingDown(Exception):
    """
    Raised to shut down from generator
    """


class XBeeModuleSim:
    def __init__(self, gs_address: bytes):
        """
        :brief: Constructor.
        In addition to constructing this, if any useful work is to be done then the rocket_callback and ground_callback attributes should be set - by default they are simply no-op functions.
        """
        assert len(gs_address) == 8
        self.gs_address = gs_address

        self._frame_parsers = {
            FrameType.TX_REQUEST: self._parse_tx_request_frame,
        }

        # Each element in each queue is a bytearray.
        self._rocket_rx_queue_packed = SimpleQueue()  # RX from RKT

        self._rocket_rx_queue = self._unpack(self._rocket_rx_queue_packed)

        # Callbacks should be of form callback(data), where data is a bytearray.
        # Making a no-op callback to prevent need for checking if callback exists.
        def nop_callback(data):
            return

        self.rocket_callback = nop_callback
        # Is called whenever data needs to be sent to the rocket through SIM - this should be the SIM send()
        # function. The callback should be thread safe.

        self.ground_callback = nop_callback
        # Is called whenever data recieved from the rocket needs to be sent to the rest of the ground station code.
        # The callback should be thread safe.

        self._shutdown_lock = RLock()
        self._is_shutting_down = False

        # Queues are IO bound.
        self._rocket_rx_thread = Thread(
            target=self._run_rocket_rx, name="xbee_sim_rocket_rx", daemon=True
        )

        self._rocket_rx_thread.start()

    def send_to_rocket(self, data):
        """
        :brief: Queue data to send to rocket following the XBee protocol.
        :param data: bytearray of data.
        """
        reserved = b"\xff\xfe"
        rx_options = b"\x02"
        self.rocket_callback(
            self._create_frame(
                FrameType.RX_INDICATOR,
                self.gs_address + reserved + rx_options + data,
            )
        )

        SENT_TO_ROCKET_EVENT.increment()

    def recieved_from_rocket(self, data):
        """
        :brief: All data incoming from the rocket should be passed into this method for processing.
        :param data: bytearray of data recieved.
        """
        self._rocket_rx_queue_packed.put(data)

    def _unpack(self, q):
        """
        :brief: Helper generator that unpacks the iterables in a given queue.
        :param q: SimpleQueue of iterables.
        :return: Yields the elements of each iterable in q, in order.
        """
        while True:
            arr = q.get()

            if arr is None:  # Probably a shutdown signal
                with self._shutdown_lock:
                    if self._is_shutting_down:
                        raise ShuttingDown()

            for i in arr:
                yield i

    def _run_rocket_rx(self) -> None:
        """
        :brief: Process the incoming rocket data queue.
        This is the top level function, and handles any unescaped start delimiters.
        """
        LOGGER.debug(f"Xbee sim thread started")

        while True:
            try:
                start = next(self._rocket_rx_queue)
                assert start == START_DELIMITER
                self._parse_API_frame()
            except UnescapedDelimiterError:
                LOGGER.warning("Caught UnescapedDelimiterError exception")
                continue  # drop it and try again
            except ShuttingDown:
                break

        LOGGER.warning("Xbee sim thread shut down")

    def shutdown(self):
        with self._shutdown_lock:
            self._is_shutting_down = True

        self._rocket_rx_queue_packed.put(None)  # Wake up thread

        self._rocket_rx_thread.join()

    # Each frame parser gets iterator to data and the length (as given by the XBee frame standard).
    # Note that since the length as given by the XBee standard includes the frame type, but the frame
    # type is not passed to each frame parser, parsers should take in length - 1 bytes. Data iterator
    # may throw StopIteration; do not catch this.
    def _parse_tx_request_frame(self, data, frame_len) -> None:
        """
        :brief: Parses a TX Request frame, and passes a TX Status packet to the rocket.
        :param data: Iterable
        :param frame_len: length as defined in XBee protocol
        """
        calculated_checksum = FrameType.TX_REQUEST.value  # Checksum includes frame type

        frame_id = next(data)
        calculated_checksum += frame_id

        destination_address = bytearray()
        for _ in range(8):  # 64 bit destination address
            b = next(data)
            destination_address.append(b)
            calculated_checksum += b

        # Reserved 2 bytes. But in one case it's labelled as network address?
        network_addr_msb = next(data)
        calculated_checksum += network_addr_msb

        network_addr_lsb = next(data)
        calculated_checksum += network_addr_lsb

        broadcast_radius = next(data)  # Broadcast radius - not used
        calculated_checksum += broadcast_radius

        transmit_options = next(data)
        calculated_checksum += transmit_options

        payload = bytearray()
        for _ in range(frame_len - 14):
            b = next(data)
            payload.append(b)
            calculated_checksum += b

        received_checksum = next(data)
        calculated_checksum = 0xFF - (calculated_checksum & 0xFF)  # As per XBee's spec

        if received_checksum != calculated_checksum:
            raise ChecksumMismatchError()

        if destination_address == bytearray(
            self.gs_address
        ) or destination_address == bytearray(XBEE_BROADCAST_ADDRESS):
            self.ground_callback(payload)
        else:
            LOGGER.warning(
                f"Discarding tx request frame with destination address other than GS ({destination_address.hex()})"
            )

        # Send acknowledge
        status_payload = bytearray(
            (frame_id, network_addr_msb, network_addr_lsb, 0, 0, 0)
        )
        self.rocket_callback(self._create_frame(FrameType.TX_STATUS, status_payload))

    def _parse_API_frame(self) -> None:
        """Parses one XBee API frame based on the rocket_rx_queue."""

        def unescape(q):
            """
            :brief: Undos the escaping in the XBee protocol standard
            :param q: Unpacked queue (with escaped characters)
            """
            for char in q:
                if char == START_DELIMITER:
                    raise UnescapedDelimiterError
                elif char == ESCAPE_CHAR:
                    char = next(q) ^ ESCAPE_XOR
                yield char

        unescaped = unescape(self._rocket_rx_queue)
        frame_len = next(unescaped) << 8
        frame_len += next(unescaped)
        frame_type = next(unescaped)
        assert frame_type in self._frame_parsers
        self._frame_parsers[frame_type](unescaped, frame_len)

        FRAME_PARSED_EVENT.increment()

    def _escape(self, unescaped) -> bytearray:
        """
        :param unescaped: Data to be escaped.
        :type unescaped: iterable of byte (e.g. bytes, bytearray)
        :return: Escaped data.
        :rtype: bytearray
        """
        escaped = bytearray()
        for b in unescaped:
            if b in NEEDS_ESCAPING:
                escaped.append(ESCAPE_CHAR)
                escaped.append(b ^ ESCAPE_XOR)
            else:
                escaped.append(b)
        return escaped

    def _create_frame(self, frame_type, payload):
        """
        Creates a frame.
        :param frame_type: int specifying the type of the frame
        :param payload: bytearray containing frame data.
        :return: bytearray containing the full frame.
        """
        frame_len = len(payload) + 1
        assert frame_len < (1 << 16)  # i.e. can be stored in 2 bytes
        len_lsb = frame_len & 0xFF
        len_msb = frame_len >> 8

        checksum = 0xFF - ((frame_type + sum(payload)) & 0xFF)
        unescaped = (
            bytearray((len_msb, len_lsb, frame_type)) + payload + bytearray((checksum,))
        )

        return bytes((START_DELIMITER,)) + self._escape(unescaped)
