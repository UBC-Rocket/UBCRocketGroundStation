import collections
import math
import struct
from enum import Enum
from io import BytesIO
from typing import Any, Callable, Dict, List

from . import subpacket_ids
from util.detail import LOGGER, Count
from util.event_stats import Event
from .subpacket_ids import SubpacketEnum

BULK_SENSOR_EVENT = Event('bulk_sensor')
SINGLE_SENSOR_EVENT = Event('single_sensor')
CONFIG_EVENT = Event('config')

# Essentially a mini-class, to structure the header data. Doesn't merit its own class due to limited use,
# can be expanded if necessary elsewhere.
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp', 'header_length', 'data_length', 'total_length'])

# CONSTANTS
# TODO Extract
ROCKET_TYPE = 'ROCKET_TYPE'
IS_SIM = 'IS_SIM'
VERSION_ID = 'VERSION_ID'
VERSION_ID_LEN = 40 # TODO Could instead use passed length parameter, if this is not necessary
MESSAGE = 'MESSAGE'
# TODO extract and cleanup https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
NOMINAL = 'NOMINAL'
NONCRITICAL_FAILURE = 'NONCRITICAL_FAILURE'
CRITICAL_FAILURE = 'CRITICAL_FAILURE'
OVERALL_STATUS = 'OVERALL_STATUS'
BAROMETER = 'BAROMETER'
GPS = 'GPS'
ACCELEROMETER = 'ACCELEROMETER'
TEMPERATURE = 'TEMPERATURE'
IMU = 'IMU'
SENSOR_TYPES = [BAROMETER, GPS, ACCELEROMETER, IMU, TEMPERATURE]
DROGUE_IGNITER_CONTINUITY = 'DROGUE_IGNITER_CONTINUITY'
MAIN_IGNITER_CONTINUITY = 'MAIN_IGNITER_CONTINUITY'
FILE_OPEN_SUCCESS = 'FILE_OPEN_SUCCESS'
OTHER_STATUS_TYPES = [DROGUE_IGNITER_CONTINUITY, MAIN_IGNITER_CONTINUITY, FILE_OPEN_SUCCESS]

class ClientType(Enum):
    TANTALUS_STAGE_1 = 0x00
    TANTALUS_STAGE_2 = 0x01
    CO_PILOT = 0x02

# Map subpacket id to DATA length (excluding header) in bytes. Only includes types with CONSTANT lengths.
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    SubpacketEnum.STATUS_PING.value: 5,
    SubpacketEnum.EVENT.value: 1,
    SubpacketEnum.CONFIG.value: 42,
    SubpacketEnum.GPS.value: 12,
    SubpacketEnum.ORIENTATION.value: 16,
    SubpacketEnum.BULK_SENSOR.value: 37,
}
for i in subpacket_ids.get_list_of_sensor_IDs():
    PACKET_ID_TO_CONST_LENGTH[i] = 4

HEADER_SIZE_WITH_LEN = 6
HEADER_SIZE_NO_LEN = 5

# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()


# This class takes care of converting subpacket data coming in, according to the specifications.
class PacketParser:

    def __init__(self, bigEndianInts, bigEndianFloats):
        """

        :param bigEndianInts:
        :type bigEndianInts:
        :param bigEndianFloats:
        :type bigEndianFloats:
        """
        self.bigEndianInts = bigEndianInts
        self.bigEndianFloats = bigEndianFloats

    def extract(self, byte_stream: BytesIO):
        """
        Return dict of parsed subpacket data and length of subpacket

        :param byte_stream:
        :type byte_stream:
        :return: parsed_data
        :rtype: Dict[Any, Any]
        """
        # header extraction
        header: Header = self.header(byte_stream)

        # data extraction
        parsed_data: Dict[Any, Any] = {}
        try:
            parsed_data = self.parse_data(byte_stream, header.subpacket_id, header.data_length)
        except Exception as e:
            LOGGER.exception("Error parsing data")  # Automatically grabs and prints exception info

        parsed_data[SubpacketEnum.TIME.value] = header.timestamp
        return parsed_data

    def parse_data(self, byte_stream: BytesIO, subpacket_id: int, length: int) -> Dict[Any, Any]:
        """
         General data parser interface. Routes to the right parser, based on subpacket_id.

        :param subpacket_id:
        :type subpacket_id:
        :param byte_stream:
        :type byte_stream:
        :param length:
        :type length:
        :return:
        :rtype:
        """
        return self.packetTypeToParser[subpacket_id](self, byte_stream, subpacket_id=subpacket_id, length=length)

    def header(self, byte_stream: BytesIO) -> Header:
        """
        Header extractor helper.
        ASSUMES that length values represent data length excluding header

        :param byte_stream:
        :type byte_stream:
        :return:
        :rtype:
        """
        # Get ID
        subpacket_id: int = byte_stream.read(1)[0]

        # check that id is valid:
        if not subpacket_ids.isSubpacketID(subpacket_id):
            LOGGER.error("Subpacket id %d not valid.", subpacket_id)
            raise ValueError("Subpacket id " + str(subpacket_id) + " not valid.")

        # Get timestamp
        timestamp: int = self.fourtoint(byte_stream.read(4))

        # Get length
        if isPacketLengthConst(subpacket_id):
            data_length: int = PACKET_ID_TO_CONST_LENGTH[subpacket_id]
            header_length = HEADER_SIZE_NO_LEN
        else:
            data_length: int = byte_stream.read(1)[0]
            header_length = HEADER_SIZE_WITH_LEN

        total_length = data_length + header_length

        return Header(subpacket_id, timestamp, header_length, data_length, total_length)

    ### General sensor data parsers

    def status_ping(self, byte_stream: BytesIO, **kwargs):
        """
        Convert bit field into a series of statuses

        :param byte_stream:
        :type byte_stream:
        :key ---: unused
        :return:
        :rtype:
        """
        sensor_bit_field_length = 16
        other_bit_field_length = 16

        data: Dict = {}
        curr_byte: int = byte_stream.read(1)[0]

        # Overall status from 6th and 7th bits
        overall_status = self.bitfrombyte(curr_byte, 1) | self.bitfrombyte(curr_byte, 0)
        if overall_status == 0b00000000:
            data[SubpacketEnum.STATUS_PING.value] = NOMINAL
        elif overall_status == 0b00000001:
            data[SubpacketEnum.STATUS_PING.value] = NONCRITICAL_FAILURE
        elif overall_status == 0b00000011:
            data[SubpacketEnum.STATUS_PING.value] = CRITICAL_FAILURE
        data[OVERALL_STATUS] = curr_byte # TODO Review if safer this way
        LOGGER.info("Overall rocket status: %s", str(data[SubpacketEnum.STATUS_PING.value]))

        # save since we do multiple passes over each byte
        byte_list: List[int] = [b for b in byte_stream.read(2)]
        # Sensor status
        num_assigned_bits = min(sensor_bit_field_length, len(SENSOR_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = math.floor(i / 8) # 0 based index, of byte out of current group
            relative_bit_index = 7 - (i % 8)  # get the bits left to right
            data[SENSOR_TYPES[i]] = self.bitfrombyte(byte_list[byte_index], relative_bit_index)

        byte_list: List[int] = [b for b in byte_stream.read(2)]
        # Other misc statuses
        num_assigned_bits = min(other_bit_field_length, len(OTHER_STATUS_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = math.floor(i / 8)
            relative_bit_index = 7 - (i % 8)
            data[OTHER_STATUS_TYPES[i]] = self.bitfrombyte(byte_list[byte_index], relative_bit_index)

        LOGGER.info(" - status of sensors" + ", %s" * len(SENSOR_TYPES),
                    *[sensor + ": " + str(data[sensor]) for sensor in SENSOR_TYPES])
        LOGGER.info(" - status of others" + ", %s" * len(OTHER_STATUS_TYPES),
                    *[other + ": " + str(data[other]) for other in OTHER_STATUS_TYPES])
        return data

    def message(self, byte_stream: BytesIO, **kwargs):
        """
        Save and log an extracted message.

        :param byte_stream:
        :type byte_stream:
        :key length: Message size in bytes
        :return:
        :rtype:
        """
        data: Dict = {}
        length = kwargs['length']

        # Two step: immutable int[] -> string
        byte_data = byte_stream.read(length)
        data[SubpacketEnum.MESSAGE.value] = byte_data.decode('ascii')

        # Do something with data
        LOGGER.info("Incoming message: " + str(data[SubpacketEnum.MESSAGE.value]))
        return data

    def event(self, byte_stream: BytesIO, **kwargs):
        """

        :param byte_stream:
        :type byte_stream:
        :key ---: unused
        :return:
        :rtype:
        """
        data: Dict = {}
        # TODO Enumerate the list of events mapped to strings somewhere? Then convert to human readable string here. https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
        data[SubpacketEnum.EVENT.value] = byte_stream.read(1)[0]
        return data

    def config(self, byte_stream: BytesIO, **kwargs):
        """

        :param byte_stream:
        :type byte_stream:
        :key ---: unused
        :return:
        :rtype:
        """

        data = {}
        data[IS_SIM] = byte_stream.read(1)[0]
        data[ROCKET_TYPE] = ClientType(byte_stream.read(1)[0])
        version_id = byte_stream.read(VERSION_ID_LEN)
        data[VERSION_ID] = version_id.decode('ascii')

        LOGGER.info("Config: SIM? %s, Rocket type = %s, Version ID = %s",
                    str(data[IS_SIM]),
                    str(data[ROCKET_TYPE]),
                    str(data[VERSION_ID]))

        CONFIG_EVENT.increment()
        return data

    def single_sensor(self, byte_stream: BytesIO, **kwargs):
        """

        :param byte_stream:
        :type byte_stream:
        :key subpacket_id: The type of sensor, but mapped to subpacket id TODO Review w/ https://trello.com/c/uFHtaN51 https://trello.com/c/bA3RuHUC
        :return:
        :rtype:
        """
        subpacket_id = kwargs['subpacket_id']
        data = {}
        # TODO Commented out, since apparently we pass along state, and other non-floats items, as float too??
        # if subpacket_id == SubpacketEnum.STATE.value:
        #     data[subpacket_id] = byte_list[0]
        # else:
        #     data[subpacket_id] = self.fourtofloat(byte_list[0])
        data[subpacket_id] = self.fourtofloat(byte_stream.read(4))

        SINGLE_SENSOR_EVENT.increment()
        return data

    def gps(self, byte_stream: BytesIO, **kwargs):
        """

        :param byte_stream:
        :type byte_stream:
        :key ---: unused
        :return:
        :rtype:
        """
        data = {}
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.GPS_ALTITUDE.value] = self.fourtofloat(byte_stream.read(4))
        return data

    def orientation(self, byte_stream: BytesIO, **kwargs):
        """

        :param byte_stream:
        :type byte_stream:
        :key ---: unused
        :return:
        :rtype:
        """
        data = {}

        # TODO Temporary dependency on subpacket enum, til we figure out https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_4.value] = self.fourtofloat(byte_stream.read(4))
        return data

    def bulk_sensor(self, byte_stream: BytesIO, **kwargs):
        """

        :param byte_stream:
        :type byte_stream:
        :key ---: unused
        :return:
        :rtype:
        """
        data: Dict[int, Any] = {}

        data[SubpacketEnum.CALCULATED_ALTITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ACCELERATION_X.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ACCELERATION_Y.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ACCELERATION_Z.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(byte_stream.read(4)) # TODO Remove soon?
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(byte_stream.read(4)) # TODO Remove soon?
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(byte_stream.read(4)) # TODO Remove soon?
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.STATE.value] = int.from_bytes(byte_stream.read(1), "big")

        BULK_SENSOR_EVENT.increment()
        return data


    # Dictionary of subpacket id mapped to function to parse that data
    packetTypeToParser: Dict[int, Callable[[BytesIO, Any], Dict[Any, Any]]] = {
        SubpacketEnum.STATUS_PING.value: status_ping,
        SubpacketEnum.MESSAGE.value: message,
        SubpacketEnum.EVENT.value: event,
        SubpacketEnum.CONFIG.value: config,
        SubpacketEnum.GPS.value: gps,
        SubpacketEnum.ORIENTATION.value: orientation,
        SubpacketEnum.BULK_SENSOR.value: bulk_sensor,
        # SubpacketEnum.SINGLE_SENSOR.value: single_sensor,  # See loop that maps function for range of ids below
    }
    for i in subpacket_ids.get_list_of_sensor_IDs():
        packetTypeToParser[i] = single_sensor

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
        c = struct.unpack('>f' if self.bigEndianFloats else '<f', b)
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
        c = struct.unpack('>I' if self.bigEndianInts else '<I', b)
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
