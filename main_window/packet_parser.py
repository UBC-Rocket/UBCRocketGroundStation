import collections
import struct
from enum import Enum
from .device_manager import DeviceType
from io import BytesIO
from typing import Any, Callable, Dict

from util.detail import LOGGER
from util.event_stats import Event
from main_window.data_entry_id import DataEntryIds, DataEntryValues


SINGLE_SENSOR_EVENT = Event('single_sensor')
CONFIG_EVENT = Event('config')
EVENT_EVENT = Event('event')
STATE_EVENT = Event('event')

# Essentially a mini-class, to structure the header data. Doesn't merit its own class due to limited use,
# can be expanded if necessary elsewhere.
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp'])

# Parser's subpacket ids. Should not be used elsewhere, NOT DataIds
class SubpacketIds(Enum):
    MESSAGE = 0x01
    EVENT = 0x02
    CONFIG = 0x03
    STATE = 0x05
    # SINGLE_SENSOR's many values, added dynamically in constructor
    ACCELERATION_X = 0x10
    ACCELERATION_Y = 0x11
    ACCELERATION_Z = 0x12
    PRESSURE = 0x13
    BAROMETER_TEMPERATURE = 0x14
    TEMPERATURE = 0x15
    LATITUDE = 0x19
    LONGITUDE = 0x1A
    GPS_ALTITUDE = 0x1B
    CALCULATED_ALTITUDE = 0x1C
    VOLTAGE = 0x1E
    GROUND_ALTITUDE = 0x1F
    TIME = 0x20
    ORIENTATION_1 = 0x21 # TODO Remove once dependencies can be resolved. Relates to https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
    ORIENTATION_2 = 0x22 # TODO Remove
    ORIENTATION_3 = 0x23 # TODO Remove
    ORIENTATION_4 = 0x24 # TODO Remove

VERSION_ID_LEN = 40

# Range from spec. single_sensor depends on this
MIN_SINGLE_SENSOR_ID: int = 0x10
MAX_SINGLE_SENSOR_ID: int = 0x2F


ID_TO_DEVICE_TYPE = {
        0x00: DeviceType.BNB_STAGE_1_FLARE,
        0x01: DeviceType.BNB_STAGE_2_FLARE,
        0x02: DeviceType.CO_PILOT_FLARE,
        0x03: DeviceType.HOLLYBURN_BODY_FLARE,
        0x04: DeviceType.HOLLYBURN_NOSE_FLARE,
        0x05: DeviceType.SILVERTIP_FLARE
}
DEVICE_TYPE_TO_ID = {y: x for (x, y) in ID_TO_DEVICE_TYPE.items()}

# NOTE: Must match enum ids in radio spec (and FLARE: radio.h)
EVENT_IDS = {
    0x00: DataEntryValues.EVENT_IGNITOR_FIRED,
    0x01: DataEntryValues.EVENT_LOW_VOLTAGE
}
STATE_IDS = {
    0x00: DataEntryValues.STATE_STANDBY,
    0x01: DataEntryValues.STATE_ARMED,
    0x02: DataEntryValues.STATE_POWERED_ASCENT,
    0x03: DataEntryValues.STATE_PRE_AIR_START_COAST_TIMED,
    0x04: DataEntryValues.STATE_ASCENT_TO_APOGEE,
    0x05: DataEntryValues.STATE_MACH_LOCK,
    0x06: DataEntryValues.STATE_PRESSURE_DELAY,
    0x07: DataEntryValues.STATE_DROGUE_DESCENT,
    0x08: DataEntryValues.STATE_MAIN_DESCENT,
    0x09: DataEntryValues.STATE_LANDED,
    0x0A: DataEntryValues.STATE_WINTER_CONTINGENCY,
}


class PacketParser:
    """
    This class takes care of converting subpacket data coming in, according to the specifications.
    """

    def __init__(self):
        """

        :param bigEndianInts:
        :type bigEndianInts:
        :param bigEndianFloats:
        :type bigEndianFloats:
        """
        self.big_endian_ints = None
        self.big_endian_floats = None

        # Dictionary of subpacket id mapped to function to parse that data
        self.packet_type_to_parser: Dict[int, Callable[[BytesIO, Header], Dict[Any, Any]]] = {
            SubpacketIds.MESSAGE.value: self.message,
            SubpacketIds.EVENT.value: self.event,
            SubpacketIds.CONFIG.value: self.config,
            SubpacketIds.STATE.value: self.state,
            # SubpacketIds.SINGLE_SENSOR.value: single_sensor,  # See loop that maps function for range of ids below
        }
        for i in range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID + 1):
            self.packet_type_to_parser[i] = self.single_sensor

    @property
    def header_size(self):
        """
        Essentially a constant field belonging to PacketParser.
        """
        return 5

    def set_endianness(self, big_endian_ints: bool, big_endian_floats: bool):
        self.big_endian_ints = big_endian_ints
        self.big_endian_floats = big_endian_floats

    def extract(self, byte_stream: BytesIO):
        """
        Return dict of parsed subpacket data and length of subpacket

        :param byte_stream:
        :type byte_stream:
        :return: parsed_data
        :rtype: Dict[Any, Any]
        """
        if self.big_endian_ints is None or self.big_endian_floats is None:
            raise Exception("Endianness not set before parsing")

        # header extraction
        header: Header = self.header(byte_stream)

        # data extraction
        parsed_data: Dict[Any, Any] = {}
        try:
            parsed_data = self.parse_data(byte_stream, header)
        except Exception as e:
            LOGGER.exception("Error parsing data")  # Automatically grabs and prints exception info

        parsed_data[DataEntryIds.TIME] = header.timestamp

        self.big_endian_ints = None
        self.big_endian_floats = None
        return parsed_data

    def parse_data(self, byte_stream: BytesIO, header: Header) -> Dict[Any, Any]:
        """
         General data parser interface. Routes to the right parser, based on subpacket_id.

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        return self.packet_type_to_parser[header.subpacket_id](byte_stream, header)

    def header(self, byte_stream: BytesIO) -> Header:
        """
        Header extractor helper.

        :param byte_stream:
        :type byte_stream:
        :return:
        :rtype:
        """
        # Get ID
        subpacket_id: int = byte_stream.read(1)[0]

        # check that id is valid:
        if subpacket_id not in self.packet_type_to_parser:
            LOGGER.error("Subpacket id %d not valid.", subpacket_id)
            raise ValueError("Subpacket id " + str(subpacket_id) + " not valid.")

        # Get timestamp
        timestamp: int = self.bytestoint(byte_stream.read(4))

        return Header(subpacket_id, timestamp)

    def message(self, byte_stream: BytesIO, header: Header):
        """
        Save and log an extracted message.

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        data: Dict = {}
        length: int = byte_stream.read(1)[0]

        # Two step: immutable int[] -> string
        byte_data = byte_stream.read(length)
        data[DataEntryIds.MESSAGE] = byte_data.decode('ascii')

        # Do something with data
        LOGGER.info("Incoming message: " + str(data[DataEntryIds.MESSAGE]))
        return data

    def event(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        """
        data: Dict = {}
        event_bytes = byte_stream.read(2)
        event_int = self.bytestoint(event_bytes)
        data_entry_value = EVENT_IDS[event_int]
        data[DataEntryIds.EVENT] = data_entry_value

        LOGGER.info("Event: %s", str(data_entry_value.name))
        EVENT_EVENT.increment()
        return data

    def config(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """

        data = {}
        data[DataEntryIds.IS_SIM] = bool(byte_stream.read(1)[0])
        data[DataEntryIds.DEVICE_TYPE] = ID_TO_DEVICE_TYPE[byte_stream.read(1)[0]]
        version_id = byte_stream.read(VERSION_ID_LEN)
        data[DataEntryIds.VERSION_ID] = version_id.decode('ascii')

        LOGGER.info("Config: SIM? %s, Rocket type = %s, Version ID = %s",
                    str(data[DataEntryIds.IS_SIM]),
                    str(data[DataEntryIds.DEVICE_TYPE]),
                    str(data[DataEntryIds.VERSION_ID]))

        CONFIG_EVENT.increment()
        return data

    def state(self, byte_stream: BytesIO, header: Header, print_state=True):
        """

        :param byte_stream:
        :param header:
        :return:
        """
        data = {}
        state_id = self.bytestoint(byte_stream.read(2))
        data_entry_value = STATE_IDS[state_id]
        data[DataEntryIds.STATE] = data_entry_value

        if print_state:
            LOGGER.info("State: %s", str(data_entry_value.name))

        STATE_EVENT.increment()
        return data

    def single_sensor(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        # Transform int single sensor id to global DataEntryId
        data_id = DataEntryIds[SubpacketIds(header.subpacket_id).name]

        data: Dict = {}
        data[data_id] = self.fourtofloat(byte_stream.read(4))

        SINGLE_SENSOR_EVENT.increment()
        return data

    def register_packet(self, packetType: int, parsing_fn: Callable[[BytesIO, Header], Dict[Any, Any]]):
        self.packet_type_to_parser[packetType] = parsing_fn

    # TODO Put these in utils folder/file?
    def fourtofloat(self, byte_list):
        """

        :param bytes:
        :type bytes:
        :return:
        :rtype:
        """
        assert len(byte_list) == 4
        data = byte_list
        b = struct.pack('4B', *data)
        c = struct.unpack('>f' if self.big_endian_floats else '<f', b)
        return c[0]

    def bytestoint(self, byte_list: list):
        """
        Returns the integer representation of a list of bytes.

        :param byte_list the bytes list from which to build the integer.
               Endianness follows config packet.
        :return: the integer
        """
        return int.from_bytes(byte_list, 'big' if self.big_endian_ints else 'little')

    def bitfrombyte(self, val: int, targetIndex: int):
        """
        Helper function. Extract bit at position targetIndex. 0 based index.

        :param val:
        :type int:
        :param targetIndex:
        :type int:
        :return: extracted bit
        :rtype: int
        """
        mask = 0b1 << targetIndex
        bit = val & mask
        bit = bit >> targetIndex
        return bit
