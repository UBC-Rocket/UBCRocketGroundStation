import math
from typing import Dict, Any, Callable, Union, List, Tuple
import struct
import SubpacketIDs
from SubpacketIDs import SubpacketEnum

import collections
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp', 'header_length', 'data_length', 'total_length'])

# CONSTANTS

# Map subpacket id to DATA length (excluding header) in bytes. Only includes types with CONSTANT lengths.
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    SubpacketEnum.STATUS_PING.value: 5,
    SubpacketEnum.EVENT.value: 1,
    SubpacketEnum.GPS.value: 24,
    SubpacketEnum.ACKNOWLEDGEMENT.value: 0000,  # TODO ack length??
    SubpacketEnum.BULK_SENSOR.value: 37,
}
for i in SubpacketIDs.get_list_of_sensor_IDs():
    PACKET_ID_TO_CONST_LENGTH[i] = 4

# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()


# # TODO remove? since we have header helper that tracks header size. Would be useful, if header size varies more
# # Map subpacket id to header size in bytes. Only includes types with CONSTANT lengths
# PACKET_ID_TO_HEADER_SIZE: Dict[int, int] = {
#     SubpacketEnum.STATUS_PING.value: 5,
#     SubpacketEnum.MESSAGE.value: 6,
#     SubpacketEnum.EVENT.value: 5,
#     SubpacketEnum.CONFIG.value: 5,
#     SubpacketEnum.GPS.value: 5,
#     SubpacketEnum.ACKNOWLEDGEMENT.value: ,???
#     SubpacketEnum.BULK_SENSOR.value: 5,
# }
# for i in SubpacketIDs.get_list_of_sensor_IDs():
#     PACKET_ID_TO_HEADER_SIZE[i] = 1

# This class takes care of converting subpacket data coming in, according to the specifications.
# The term/parameter name byte list refer to a list of byte data, each byte being represented as ints.
class RadioController:

    def __init__(self, bigEndianInts, bigEndianFloats):
        self.bigEndianInts = bigEndianInts
        self.bigEndianFloats = bigEndianFloats

    # Return dict of parsed subpacket data and length of subpacket
    def extract(self, byte_list: List):
        # header extraction
        header = self.header(byte_list)
        # data extraction
        data_unit = byte_list[header.header_length:header.total_length]
        data_length = header.data_length
        try:
            parsed_data: Dict[any, any] = self.parse_data(header.subpacket_id, data_unit, data_length)
        except Exception as e:
            print(e)
            raise e
        # Add timestamp from header
        parsed_data[SubpacketEnum.TIME.value] = header.timestamp
        return parsed_data, header.total_length

    # Helper to convert byte to subpacket id as is in the SubpacketID enum, throws error otherwise
    def extract_subpacket_ID(self, byte: List):
        # subpacket_id: int = int.from_bytes(byte, "big")
        subpacket_id: int = byte
        # check that id is valid:
        if not SubpacketIDs.isSubpacketID(subpacket_id):
            # TODO Error log here?
            raise ValueError
        return SubpacketEnum(subpacket_id).value


    # general data parser interface. Routes to the right parse, based on type_id
    def parse_data(self, type_id, byte_list, length) -> Dict[any, any]:
        print(type_id, byte_list)
        # Switch, passing Id if it is a sensor type
        return self.packetTypeToParser[type_id](self, byte_list, length=length, type_id=type_id)
        # if SubpacketIDs.isSingleSensorData(type_id):
        #     return self.packetTypeToParser[type_id](self, byte_list, length=length, type_id=type_id)
        # else:
        #     return self.packetTypeToParser[type_id](self, byte_list, length=length, type_id=type_id)

    # Header extractor helper.
    # ASSUMES that length values represent full subpacket lengths, including headers
    def header(self, byte_list: List) -> Header:
        currByte = Count(0, 1)  # index for which byte is to be processed next. Collected in return as header size
        # Get ID
        subpacket_id: int = self.extract_subpacket_ID(byte_list[currByte.currAndInc(1)])

        # Get timestamp
        timestamp: int = self.fourtoint(byte_list[currByte.curr(): currByte.next(4)])

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
        sensor_bit_field_length = 16
        other_bit_field_length = 16
        # TODO need these elsewhere? extract (and make enum, or maybe combine with SubpacketIds somehow)
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
        overallStatus = bitFromByte(byte_list[curr_byte.curr()], 1) | bitFromByte(byte_list[curr_byte.currAndInc(1)], 0)
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
            data[SENSOR_TYPES[i]] = bitFromByte(byte_list[byte_index], relative_bit_index)
        curr_byte.next(math.floor(sensor_bit_field_length / 8))  # move to next section of bytes

        # Other misc statuses
        num_assigned_bits = min(other_bit_field_length, len(OTHER_STATUS_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = curr_byte.curr() + math.floor(i / 8)
            relative_bit_index = 7 - (i % 8)
            data[OTHER_STATUS_TYPES[i]] = bitFromByte(byte_list[byte_index], relative_bit_index)
        curr_byte.next(math.floor(other_bit_field_length / 8))
        return data

    def message(self, byte_list, **kwargs):
        data: Dict = {}

        # Two step: int[] -> bytearray -> string. Probably a more efficient way
        byte_data = bytearray(byte_list)
        data[SubpacketEnum.MESSAGE.value] = byte_data.decode('ascii')
        print(data[SubpacketEnum.MESSAGE.value])  # TODO Temporary until: saving to RocketData, logging, or displaying done
        return data

    def event(self, byte_list, **kwargs):
        data: Dict = {}
        # TODO Enumerate the list of events mapped to strings somewhere? Then convert to human readable string here.
        data[SubpacketEnum.EVENT.value] = byte_list[0]
        return data

    # TODO. This is a stub until there is a spec.
    def config(self, byte_list, **kwargs):
        data = {}
        data[SubpacketEnum.CONFIG.value] = byte_list[0]
        return data

    def single_sensor(self, byte_list, **kwargs):
        type_id = kwargs['type_id']
        data = {}
        # TODO Commented out, since apparently we pass along state, or other non-floats as float too??
        # if type_id == SubpacketEnum.STATE.value:
        #     data[type_id] = byte_list[0]
        # else:
        #     data[type_id] = self.fourtofloat(byte_list[0])
        data[type_id] = self.fourtofloat(byte_list[0])
        return data

    def gps(self, byte_list, **kwargs):
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
        data: Dict[int, any] = {}

        # # TODO REVIEW/CHANGE in type refactoring: how this is required to convert from List[bytes] to List[int]
        # byte_list: List[int] = [int(x[0]) for x in byte_list]
        curr_byte = Count(0, 4)

        data[SubpacketEnum.CALCULATED_ALTITUDE.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])  # TODO Double check it is calculated barometer altitude with firmware
        data[SubpacketEnum.ACCELERATION_X.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.ACCELERATION_Y.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.ACCELERATION_Z.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])  # TODO Should lat+lon be doubles??
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(byte_list[curr_byte.curr():curr_byte.next(4)])
        data[SubpacketEnum.STATE.value] = byte_list[curr_byte.currAndInc(1)]
        return data


    # Dictionary of subpacket id mapped to function to parse that data
    packetTypeToParser: Dict[int, Callable[[list, int], Dict[any, any]]] = {  # TODO review this type hint
        SubpacketEnum.STATUS_PING.value: statusPing,
        SubpacketEnum.MESSAGE.value: message,
        SubpacketEnum.EVENT.value: event,
        SubpacketEnum.CONFIG.value: config,
        # SubpacketEnum.SINGLE_SENSOR.value: single_sensor,  # See loop that maps function for range of ids below
        SubpacketEnum.GPS.value: gps,
        # SubpacketEnum.ACKNOWLEDGEMENT.value: acknowledgement,
        SubpacketEnum.BULK_SENSOR.value: bulk_sensor,
    }
    for i in SubpacketIDs.get_list_of_sensor_IDs():
        packetTypeToParser[i] = single_sensor

    # TODO Put these in utils folder/file?
    def fourtofloat(self, byte_list):
        assert len(byte_list) == 4
        data = byte_list
        b = struct.pack('4B', *data)
        c = struct.unpack('>f' if self.bigEndianFloats else '<f', b)
        return c[0]

    def fourtoint(self, byte_list):
        assert len(byte_list) == 4
        data = byte_list
        b = struct.pack('4B', *data)
        c = struct.unpack('>I' if self.bigEndianInts else '<I', b)
        return c[0]

    def eighttodouble(self, byte_list):
        assert len(byte_list) == 8
        data = byte_list
        b = struct.pack('8B', *data)
        c = struct.unpack('>d' if self.bigEndianInts else '<d', b)
        return c[0]

# Helper class. python way of doing ++ (unlimited incrementing) TODO Put this in utils folder/file?
class Count:
    def __init__(self, start=0, interval=1):
        self.interval = interval
        self.num = start

    def __iter__(self):
        return self

    def curr(self):
        return self.num

    # increments and returns the new value
    def next(self, interval=0):
        if interval == 0:
            self.num += self.interval
        else:
            self.num += interval

        return self.num

    # returns the current value then increments
    def currAndInc(self, interval=9):
        num = self.num
        if interval == 0:
            self.num += self.interval
        else:
            self.num += interval

        return num

# Helper function. Extract bit at position targetIndex. 0 based index. TODO Put this in utils folder/file?
def bitFromByte(val: int, targetIndex: int):
    mask = 0b1 << targetIndex
    bit = val & mask
    bit = bit >> targetIndex
    return bit
