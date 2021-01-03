import collections
import struct
from enum import Enum
from .device_manager import DeviceType
from io import BytesIO
from typing import Any, Callable, Dict

from . import data_entry_id
from util.detail import LOGGER
from util.event_stats import Event
from main_window.data_entry_id import DataEntryIds, MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID

SINGLE_SENSOR_EVENT = Event('single_sensor')
CONFIG_EVENT = Event('config')

# Essentially a mini-class, to structure the header data. Doesn't merit its own class due to limited use,
# can be expanded if necessary elsewhere.
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp'])

# Enum with packet IDs, belongin to this packet parser, and should not be used elsewhere

# Parser's subpacket ids, according to spec. NOT DataIds
class SubpacketIds(Enum):
    # STATUS_PING = 0x00
    MESSAGE = 0x01
    EVENT = 0x02
    CONFIG = 0x03
    # GPS = 0x04
    # ORIENTATION = 0x06
    # BULK_SENSOR = 0x30
# TODO Review
VERSION_ID_LEN = 40

ID_TO_DEVICE_TYPE = {
        0x00: DeviceType.TANTALUS_STAGE_1,
        0x01: DeviceType.TANTALUS_STAGE_2,
        0x02: DeviceType.CO_PILOT,
}
DEVICE_TYPE_TO_ID = {y: x for (x, y) in ID_TO_DEVICE_TYPE.items()}


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
        self.packetTypeToParser: Dict[int, Callable[[BytesIO, Header], Dict[Any, Any]]] = {
            SubpacketIds.MESSAGE.value: self.message,
            SubpacketIds.EVENT.value: self.event,
            SubpacketIds.CONFIG.value: self.config,
            # SubpacketIds.SINGLE_SENSOR.value: single_sensor,  # See loop that maps function for range of ids below
        }
        # TODO Change to actually adding ids to SubpacketId Enum instead, from range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID + 1):
        for i in data_entry_id.get_list_of_sensor_IDs():
            self.packetTypeToParser[i] = self.single_sensor

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
        return self.packetTypeToParser[header.subpacket_id](byte_stream, header)

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
        if subpacket_id not in self.packetTypeToParser:  # TODO Review: @Andrei pls check
            LOGGER.error("Subpacket id %d not valid.", subpacket_id)
            raise ValueError("Subpacket id " + str(subpacket_id) + " not valid.")

        # Get timestamp
        timestamp: int = self.fourtoint(byte_stream.read(4))

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
        :rtype:
        """
        data: Dict = {}
        # TODO Enumerate event id -> strings, and convert to human readable string here?
        data[DataEntryIds.EVENT] = byte_stream.read(1)[0]
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

    def single_sensor(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        subpacket_id = header.subpacket_id
        # Transform local subpacket id to global DataEntryId
        data_id_entry = DataEntryIds(subpacket_id)

        data: Dict = {}
        data[data_id_entry] = self.fourtofloat(byte_stream.read(4))

        SINGLE_SENSOR_EVENT.increment()
        return data

    def register_packet(self, packetType: int, parsing_fn: Callable[[BytesIO, Header], Dict[Any, Any]]):
        self.packetTypeToParser[packetType] = parsing_fn

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

    def fourtoint(self, byte_list):
        """

        :param bytes:
        :type bytes:
        :return:
        :rtype:
        """
        assert len(byte_list) == 4
        data = byte_list
        b = struct.pack('4B', *data)
        c = struct.unpack('>I' if self.big_endian_ints else '<I', b)
        return c[0]

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
