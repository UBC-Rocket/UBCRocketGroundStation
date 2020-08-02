import math
from typing import Dict, Any, Callable, Union, List, Tuple
import struct
import SubpacketIDs
from SubpacketIDs import SubpacketEnum

import collections
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp', 'header_length', 'data_length', 'total_length'])

# CONSTANTS

# TODO Review these based on spec. REVIEW Exclude header bytes???? Depends on if the 'length' field in subpackets will contain dataLength or totalLength. Will require change in extractHeader.
# Map subpacket id to DATA (excluding header) length in bytes. Only includes types with CONSTANT lengths.
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    SubpacketEnum.STATUS_PING.value: 5,
    SubpacketEnum.EVENT.value: 2,
    SubpacketEnum.GPS.value: 25,
    SubpacketEnum.ACKNOWLEDGEMENT.value: 0000,  # TODO ack length??
    SubpacketEnum.BULK_SENSOR.value: 37,  # TODO Check
}
for i in SubpacketIDs.get_list_of_sensor_IDs():
    PACKET_ID_TO_CONST_LENGTH[i] = 9

# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()


# # TODO Possibly deprecate this, since we have header helper that tracks header size
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


    # general data parser interface
    def parse_data(self, type_id, byte_list, length) -> Dict[any, any]:
        print(type_id, byte_list)
        return self.packetTypeToParser[type_id](self, byte_list, length)

    # Header extractor helper
    def header(self, byte_list: List) -> Header:
        currByte = Count(0, 1)  # index for which byte is to be processed next. Collected in return as header size
        # Get ID
        subpacket_id: int = self.extract_subpacket_ID(byte_list[currByte.currAndInc(1)])

        # Get timestamp
        # TODO REVIEW/CHANGE in type refactoring: how this is required to convert from List[bytes] to List[int]
        # Commented due to change in ReadThread, Run() line 39. Now we no longer wrap each array with another array. This appears unnecessary and is a start towards refacctoring fully
        # timestamp_int_list: List[int] = [int(x[0]) for x in byte_list[currByte.curr(): currByte.next(4)]]
        # timestamp: int = self.fourtofloat(timestamp_int_list)

        timestamp: int = self.fourtofloat(byte_list[currByte.curr(): currByte.next(4)])

        # Set header length, up to this point.
        header_length = currByte.curr()

        # Get length
        if isPacketLengthConst(subpacket_id):
            data_length: int = PACKET_ID_TO_CONST_LENGTH[subpacket_id]
        else:
            data_length: int = int.from_bytes(byte_list[currByte.currAndInc(1)], "big")
            header_length = currByte.curr() # Update header length due to presence of length byte

        total_length = data_length + header_length

        return Header(subpacket_id, timestamp, header_length, data_length, total_length)

    ### General sensor data parsers

    # Convert bit field into a series of statuses
    # FIXME Alternate implementation would convert all bytes into array of bits, then use those accordingly
    def statusPing(self, byte_list, length):
    # TODO Make actual types for statuses?
        # TODO Extract these constants
        SENSOR_BIT_FIELD_LENGTH = 16
        OTHER_BIT_FIELD_LENGTH = 16
        NOMINAL = 'NOMINAL'
        NONCRITICAL_FAILURE = "NONCRITICAL_FAILURE"
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
        currByte = Count(0, 1)

        # Overall status from 6th and 7th bits
        overallStatus = bitFromByte(byte_list[currByte.curr()], 1) | bitFromByte(byte_list[currByte.currAndInc(1)], 0)
        if overallStatus == 0b00000000:
            data['overallStatus'] = NOMINAL
        elif overallStatus == 0b00000001:
            data['overallStatus'] = NONCRITICAL_FAILURE
        elif overallStatus == 0b00000011:
            data['overallStatus'] = CRITICAL_FAILURE

        # Sensor status
        numAssignedBits = min(SENSOR_BIT_FIELD_LENGTH, len(SENSOR_TYPES))  # only go as far as is assigned
        for i in range(0, numAssignedBits):
            byteIndex = currByte.curr() + math.floor(i / 8)
            relativeBitIndex = 7 - (i % 8)  # get the bits left to right
            data[SENSOR_TYPES[i]] = bitFromByte(byte_list[byteIndex], relativeBitIndex)
        currByte.next(math.floor(SENSOR_BIT_FIELD_LENGTH / 8))  # move to next section of bytes

        # Other misc statuses
        numAssignedBits = min(OTHER_BIT_FIELD_LENGTH, len(OTHER_STATUS_TYPES))  # only go as far as is assigned
        for i in range(0, numAssignedBits):
            byteIndex = currByte.curr() + math.floor(i / 8)
            relativeBitIndex = 7 - (i % 8)
            data[OTHER_STATUS_TYPES[i]] = bitFromByte(byte_list[byteIndex], relativeBitIndex)
        currByte.next(math.floor(OTHER_BIT_FIELD_LENGTH / 8))
        return data

    def message(self, byte_list, length):  # TODO
        data: Dict = {}
        print(byte_list)
        byteData = bytearray(byte_list)
        print(byteData)
        data['MESSAGE'] = byteData.decode('ascii')
        return data

    def event(self, byte_list, length):  # TODO
        converted = {0.0}  # STUB
        return converted

    def config(self, byte_list, length):  # TODO
        converted = {0.0}  # STUB
        return converted

    def single_sensor(self, byte_list, length):  # TODO
        converted = {0.0}  # STUB
        return converted

    def gps(self, byte_list, length):  # TODO
        converted = {0.0}  # STUB
        return converted

    # def acknowledgement(self, byte_list, length):  # TODO ?
    #     converted = 0.0  # STUB
    #     return converted

    def bulk_sensor(self, byte_list: List, length: int):
        data: Dict[int, any] = {}

        # TODO REVIEW/CHANGE in type refactoring: how this is required to convert from List[bytes] to List[int]
        int_list: List[int] = [int(x[0]) for x in byte_list]
        currByte = Count(0, 4)

        data[SubpacketEnum.CALCULATED_ALTITUDE.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])  # TODO Double check it is calculated barometer altitude with firmware
        data[SubpacketEnum.ACCELERATION_X.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.ACCELERATION_Y.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.ACCELERATION_Z.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(int_list[currByte.curr():currByte.next(4)])
        data[SubpacketEnum.STATE.value] = int_list[currByte.currAndInc(1)]
        return data


    # Dictionary of subpacket id - function to parse that data
    packetTypeToParser: Dict[int, Callable[[list, int], Dict[any, any]]] = {  # TODO review this type hint
        SubpacketEnum.STATUS_PING.value: statusPing,
        SubpacketEnum.MESSAGE.value: message,
        SubpacketEnum.EVENT.value: event,
        SubpacketEnum.CONFIG.value: config,
        # SubpacketEnum.SINGLE_SENSOR.value: single_sensor, # Todo make this a range of keys?
        SubpacketEnum.GPS.value: gps,
        # SubpacketEnum.ACKNOWLEDGEMENT.value: acknowledgement, # TODO Uncomment when complete
        SubpacketEnum.BULK_SENSOR.value: bulk_sensor,
    }

    # TODO review this for data type fixes
    def fourtofloat(self, bytes):
        assert len(bytes) == 4
        data = bytes
        b = struct.pack('4B', *data)
        c = struct.unpack('>f' if self.bigEndianFloats else '<f', b)
        return c[0]

    def fourtoint(self, bytes):
        assert len(bytes) == 4
        data = bytes
        b = struct.pack('4B', *data)
        c = struct.unpack('>I' if self.bigEndianInts else '<I', b)
        return c[0]


# python way of doing ++ (unlimited incrementing) TODO Put this in utils folder/file?
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

# Extract bit at position targetIndex. 0 based index
def bitFromByte(val: int, targetIndex: int):
    mask = 0b1 << targetIndex
    bit = val & mask
    bit = bit >> targetIndex
    return bit
