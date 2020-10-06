import collections
import math
import struct
from io import BytesIO
from typing import Any, Callable, Dict, List

from . import subpacket_ids
from detail import Count
from .subpacket_ids import SubpacketEnum

# Essentially a mini-class, to structure the header data. Doesn't merit its own class due to limited use,
# can be expanded if necessary elsewhere.
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp', 'header_length', 'data_length', 'total_length'])

# CONSTANTS

# Map subpacket id to DATA length (excluding header) in bytes. Only includes types with CONSTANT lengths.
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    SubpacketEnum.STATUS_PING.value: 5,
    SubpacketEnum.EVENT.value: 1,
    SubpacketEnum.GPS.value: 24,
    # SubpacketEnum.ACKNOWLEDGEMENT.value: 0000, # TODO
    SubpacketEnum.BULK_SENSOR.value: 37,
}
for i in subpacket_ids.get_list_of_sensor_IDs():
    PACKET_ID_TO_CONST_LENGTH[i] = 4

# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()


# This class takes care of converting subpacket data coming in, according to the specifications.
# The term/parameter name byte list refer to a list of byte data, each byte being represented as ints.
class RadioController:

    def __init__(self, bigEndianInts, bigEndianFloats):
        """

        :param bigEndianInts:
        :type bigEndianInts:
        :param bigEndianFloats:
        :type bigEndianFloats:
        """
        self.bigEndianInts = bigEndianInts
        self.bigEndianFloats = bigEndianFloats

    # Return dict of parsed subpacket data and length of subpacket
    def extract(self, byte_list: List):
        """

        :param byte_list:
        :type byte_list:
        :return:
        :rtype:
        """
        # header extraction
        header = self.header(byte_list)
        # data extraction
        data_unit = byte_list[header.header_length : header.total_length]
        try:
            parsed_data: Dict[Any, Any] = self.parse_data(header.subpacket_id, data_unit, header.data_length)
        except Exception as e:
            print(e)
            raise e
        # Add timestamp from header
        parsed_data[SubpacketEnum.TIME.value] = header.timestamp
        return parsed_data, header.total_length

    # general data parser interface. Routes to the right parse, based on subpacket_id
    def parse_data(self, subpacket_id, byte_list, length) -> Dict[Any, Any]:
        """

        :param subpacket_id:
        :type subpacket_id:
        :param byte_list:
        :type byte_list:
        :param length:
        :type length:
        :return:
        :rtype:
        """
        return self.packetTypeToParser[subpacket_id](self, byte_list, length=length, subpacket_id=subpacket_id)

    # Header extractor helper.
    # ASSUMES that length values represent data lengths, including headers
    def header(self, byte_list: List) -> Header:
        """

        :param byte_list:
        :type byte_list:
        :return:
        :rtype:
        """
        currByte = Count(0, 1)  # index for which byte is to be processed next. Collected in return as header size

        # Get ID
        subpacket_id: int = byte_list[currByte.currAndInc(1)]
        # check that id is valid:
        if not subpacket_ids.isSubpacketID(subpacket_id):
            # TODO Error log here?
            raise ValueError

        # Get timestamp
        timestamp: int = self.fourtoint(byte_list[currByte.curr() : currByte.next(4)])

        # Set header length, up to this point.
        header_length = currByte.curr()

        # Get length
        if isPacketLengthConst(subpacket_id):
            data_length: int = PACKET_ID_TO_CONST_LENGTH[subpacket_id]
        else:
            data_length: int = byte_list[currByte.currAndInc(1)]
            header_length = currByte.curr()  # Update header length due to presence of length byte

        total_length = data_length + header_length

        return Header(subpacket_id, timestamp, header_length, data_length, total_length)

    ### General sensor data parsers

    # Convert bit field into a series of statuses
    def statusPing(self, byte_list, **kwargs):
        """

        :param byte_list:
        :type byte_list:
        :key ---: unused
        :return:
        :rtype:
        """
        sensor_bit_field_length = 16
        other_bit_field_length = 16
        # TODO extract and cleanup https://trello.com/c/uFHtaN51/
        NOMINAL = 'NOMINAL'
        NONCRITICAL_FAILURE = 'NONCRITICAL_FAILURE'
        CRITICAL_FAILURE = 'CRITICAL_FAILURE'
        OVERALL_STATUS = 'OVERALL_STATUS'
        BAROMETER = 'BAROMETER'
        GPS = 'GPS'
        ACCELEROMETER = 'ACCELEROMETER'
        TEMPERATURE = 'TEMPERATURE'
        IMU = 'IMU'
        SENSOR_TYPES = [OVERALL_STATUS, BAROMETER, GPS, ACCELEROMETER, IMU, TEMPERATURE]
        DROGUE_IGNITER_CONTINUITY = 'DROGUE_IGNITER_CONTINUITY'
        MAIN_IGNITER_CONTINUITY = 'MAIN_IGNITER_CONTINUITY'
        FILE_OPEN_SUCCESS = 'FILE_OPEN_SUCCESS'
        OTHER_STATUS_TYPES = [DROGUE_IGNITER_CONTINUITY, MAIN_IGNITER_CONTINUITY, FILE_OPEN_SUCCESS]

        data: Dict = {}
        curr_byte = Count(0, 1)

        # Overall status from 6th and 7th bits
        overallStatus = self.bitfrombyte(byte_list[curr_byte.curr()], 1) | self.bitfrombyte(byte_list[curr_byte.currAndInc(1)], 0)
        if overallStatus == 0b00000000:
            data[SubpacketEnum.STATUS_PING.value] = NOMINAL
        elif overallStatus == 0b00000001:
            data[SubpacketEnum.STATUS_PING.value] = NONCRITICAL_FAILURE
        elif overallStatus == 0b00000011:
            data[SubpacketEnum.STATUS_PING.value] = CRITICAL_FAILURE

        # Sensor status
        num_assigned_bits = min(sensor_bit_field_length, len(SENSOR_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = curr_byte.curr() + math.floor(i / 8)
            relative_bit_index = 7 - (i % 8)  # get the bits left to right
            data[SENSOR_TYPES[i]] = self.bitfrombyte(byte_list[byte_index], relative_bit_index)
        curr_byte.next(math.floor(sensor_bit_field_length / 8))  # move to next section of bytes

        # Other misc statuses
        num_assigned_bits = min(other_bit_field_length, len(OTHER_STATUS_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = curr_byte.curr() + math.floor(i / 8)
            relative_bit_index = 7 - (i % 8)
            data[OTHER_STATUS_TYPES[i]] = self.bitfrombyte(byte_list[byte_index], relative_bit_index)
        curr_byte.next(math.floor(other_bit_field_length / 8))
        return data

    def message(self, byte_list, **kwargs):
        """

        :param byte_list:
        :type byte_list:
        :key ---: unused
        :return:
        :rtype:
        """
        data: Dict = {}

        # Two step: int[] -> bytearray -> string. Probably a more efficient way
        byte_data = bytearray(byte_list)
        data[SubpacketEnum.MESSAGE.value] = byte_data.decode('ascii')
        # Do something with data TODO Temporary until: saved to RocketData, logged, or displayed
        print("Incoming message: ", data[SubpacketEnum.MESSAGE.value])
        return data

    def event(self, byte_list, **kwargs):
        """

        :param byte_list:
        :type byte_list:
        :key ---: unused
        :return:
        :rtype:
        """
        data: Dict = {}
        # TODO Enumerate the list of events mapped to strings somewhere? Then convert to human readable string here.
        data[SubpacketEnum.EVENT.value] = byte_list[0]
        return data

    # TODO. This is a stub until there is a spec.
    def config(self, byte_list, **kwargs):
        """

        :param byte_list:
        :type byte_list:
        :key ---: unused
        :return:
        :rtype:
        """
        # TODO Extract
        ROCKET_TYPE = 'ROCKET_TYPE'
        IS_SIM = 'IS_SIM'

        data = {}
        data[IS_SIM] = byte_list[0]
        data[ROCKET_TYPE] = byte_list[1] # TODO Extract
        return data

    def single_sensor(self, byte_list, **kwargs):
        """

        :param byte_list:
        :type byte_list:
        :key subpacket_id: The type of sensor, but mapped to subpacket id TODO Review w/ https://trello.com/c/uFHtaN51
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
        data[subpacket_id] = self.fourtofloat(byte_list[0])
        return data

    def gps(self, byte_list, **kwargs):
        """

        :param byte_list:
        :type byte_list:
        :key ---: unused
        :return:
        :rtype:
        """
        data = {}
        curr_byte = Count(0, 1)
        data[SubpacketEnum.LATITUDE.value] = self.eighttodouble(byte_list[curr_byte.curr():curr_byte.next(8)])
        data[SubpacketEnum.LONGITUDE.value] = self.eighttodouble(byte_list[curr_byte.curr():curr_byte.next(8)])
        data[SubpacketEnum.GPS_ALTITUDE.value] = self.eighttodouble(byte_list[curr_byte.curr():curr_byte.next(8)])
        return data

    # TODO
    # def acknowledgement(self, byte_list, **kwargs):
    #     data = {}  # STUB
    #     return data

    def bulk_sensor(self, byte_list: List, **kwargs):
        r"""

        :param byte_list:
        :type byte_list:
        :key ---: unused
        :return:
        :rtype:
        """
        data: Dict[int, Any] = {}
        # TODO Review experimental form, perhaps consider doing for all https://trello.com/c/5IkOjNDm/161-clean-up-bytes-types
        bytes_IO = BytesIO(bytes(byte_list))

        data[SubpacketEnum.CALCULATED_ALTITUDE.value] = self.fourtofloat(bytes_IO.read(4))  # TODO Double check it is calculated barometer altitude with firmware
        data[SubpacketEnum.ACCELERATION_X.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.ACCELERATION_Y.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.ACCELERATION_Z.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(bytes_IO.read(4))  # TODO Should lat+lon be doubles??
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(bytes_IO.read(4))
        data[SubpacketEnum.STATE.value] = int.from_bytes(bytes_IO.read(1), "big")
        return data


    # Dictionary of subpacket id mapped to function to parse that data
    packetTypeToParser: Dict[int, Callable[[list, int], Dict[Any, Any]]] = {  # TODO review this type hint
        SubpacketEnum.STATUS_PING.value: statusPing,
        SubpacketEnum.MESSAGE.value: message,
        SubpacketEnum.EVENT.value: event,
        SubpacketEnum.CONFIG.value: config,
        # SubpacketEnum.SINGLE_SENSOR.value: single_sensor,  # See loop that maps function for range of ids below
        SubpacketEnum.GPS.value: gps,
        # SubpacketEnum.ACKNOWLEDGEMENT.value: acknowledgement,
        SubpacketEnum.BULK_SENSOR.value: bulk_sensor,
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

    def eighttodouble(self, byte_list):
        """

        :param bytes:
        :type bytes:
        :return:
        :rtype:
        """
        assert len(byte_list) == 8
        data = byte_list
        b = struct.pack('8B', *data)
        c = struct.unpack('>d' if self.bigEndianInts else '<d', b)
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
