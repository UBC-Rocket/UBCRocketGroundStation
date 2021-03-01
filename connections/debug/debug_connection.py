import random
import struct
import threading
import time

import connections.debug.radio_packets as radio_packets
from main_window.packet_parser import VERSION_ID_LEN
from ..connection import Connection, ConnectionMessage
from util.detail import LOGGER, REQUIRED_FLARE
from util.event_stats import Event

ARMED_EVENT = Event('armed')
DISARMED_EVENT = Event('disarmed')

PACKET_INTERVAL_S = 2

class DebugConnection(Connection):

    def __init__(self, device_address: str, device_id: int, generate_radio_packets=True) -> None:
        """

        """
        self.device_address = device_address
        self.device_id = device_id
        self.start_time = time.time()
        self.lastSend = time.time()
        self.callback = None
        self.lock = threading.RLock()  # Protects callback variable and any other "state" variables

        self.cv = threading.Condition(self.lock)
        self._is_shutting_down = False

        self.connectionThread = threading.Thread(target=self._run, daemon=True, name="DebugConnectionThread")
        if generate_radio_packets:
            self.connectionThread.start()

    # Thread loop that creates fake data at constant interval and returns it via callback
    def _run(self) -> None:
        """

        """
        with self.cv:
            LOGGER.debug(f"Debug connection thread started (device_address={self.device_address})")
            while True:
                self.cv.wait_for(lambda: self._is_shutting_down, timeout=PACKET_INTERVAL_S)

                if self._is_shutting_down:
                    break

                if not self.callback:
                    continue

                full_arr: bytearray = bytearray()
                # full_arr.extend(self.config_mock_set_values())
                # full_arr.extend(self.message_mock_set_values())
                full_arr.extend(self.bulk_sensor_mock_random())
                # full_arr.extend(self.event_mock_set_values())
                # full_arr.extend(self.state_mock_set_values())
                # full_arr.extend(self.bad_subpacket_id_mock()) # bad id, to see handling of itself and remaining data
                full_arr.extend(self.gps_mock_random())
                full_arr.extend(self.orientation_mock_random())
                self.receive(full_arr)

            LOGGER.warning(f"Debug connection thread shut down (device_address={self.device_address})")

    def receive(self, data):
        with self.lock:

            if not self.callback:
                raise Exception("Can't receive data. Callback not set.")

            message = ConnectionMessage(device_address=self.device_address, connection=self, data=data)

            self.callback(message)

    def bulk_sensor_mock_random(self) -> bytearray:
        """

        :return:
        :rtype: bytearray
        """

        return radio_packets.bulk_sensor(self._current_millis(),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(49.260565, 49.263859),
                                         random.uniform(-123.250990, -123.246956),
                                         random.randint(0, 0x09))

    def status_ping_mock_set_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """

        return radio_packets.status_ping(self._current_millis(),
                                         radio_packets.StatusType.NON_CRITICAL_FAILURE,
                                         0b11111100,
                                         0b11111111,
                                         0b11100000,
                                         0b11111111)

    def message_mock_set_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """

        return radio_packets.message(self._current_millis(), "hello")

    def config_mock_set_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """
        assert len(REQUIRED_FLARE) == VERSION_ID_LEN
        return radio_packets.config(self._current_millis(), False, self.device_id, REQUIRED_FLARE)

    def event_mock_set_values(self) -> bytearray:
        return radio_packets.event(self._current_millis(), 0x00)

    def state_mock_set_values(self) -> bytearray:
        return radio_packets.state(self._current_millis(), 0x05)

    def gps_mock_random(self) -> bytearray:
        """

        :return:
        :rtype: bytearray
        """

        return radio_packets.gps(self._current_millis(),
                                 random.uniform(49.260565, 49.263859),
                                 random.uniform(-123.250990, -123.246956),
                                 random.randint(0, 10000))

    def orientation_mock_random(self) -> bytearray:
        """

        :return:
        :rtype: bytearray
        """

        return radio_packets.orientation(self._current_millis(),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6))


    def bad_subpacket_id_mock(self) -> bytearray:
        """

        :return:
        :rtype: bytearray
        """

        dummy: bytearray = bytearray()
        dummy.append(69)  # id
        dummy.extend((int(1234)).to_bytes(length=4, byteorder='big'))  # time
        dummy.extend(struct.pack(">f", 137137.4575))  # barometer altitud
        return dummy


    # Register callback to which we will send new data
    def registerCallback(self, fn) -> None:
        with self.lock:
            self.callback = fn

    # Send data to a specific device on this connection
    def send(self, device_address, data) -> None:
        """

        :param device_address:
        :param data:
        :type data:
        """
        if device_address != self.device_address:
            raise Exception(f"Connection does not support address={device_address}")
        self.broadcast(data)

    # Send data to all devices on this connection
    def broadcast(self, data) -> None:  # must be thead safe
        LOGGER.info(f"{data} sent to address={self.device_address} on DebugConnection")
        with self.lock:
            if data == bytes([0x41]):
                ARMED_EVENT.increment()
            elif data == bytes([0x44]):
                DISARMED_EVENT.increment()
            elif data == bytes([0x50]):
                self.receive(self.status_ping_mock_set_values())
            elif data == bytes([0x43]):
                self.receive(self.config_mock_set_values())

    def shutdown(self) -> None:
        if not self.connectionThread.is_alive():
            return

        with self.cv:
            self._is_shutting_down = True

        while self.connectionThread.is_alive():
            with self.cv:
                self.cv.notify()  # Wake up thread

        self.connectionThread.join()  # join thread

    def isIntBigEndian(self) -> bool:
        return True

    def isFloatBigEndian(self) -> bool:
        return True

    def _current_millis(self):
        return int((time.time()-self.start_time)*1000)
