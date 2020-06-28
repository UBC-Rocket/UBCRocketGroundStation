from typing import Dict, Any, Callable, Union, List, Tuple
import struct
import SubpacketIDs
from SubpacketIDs import SubpacketEnum

import collections
Header = collections.namedtuple('Header', ['subpacket_id', 'timestamp', 'header_length', 'total_length'])

# CONSTANTS

# TODO Review these based on spec
# Map subpacket id (int) to length (int) in bytes. Only includes types with CONSTANT lengths
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    SubpacketEnum.STATUS_PING.value: 4,
    SubpacketEnum.EVENT.value: 2,
    SubpacketEnum.GPS.value: 25,
    SubpacketEnum.ACKNOWLEDGEMENT.value: 0000,  # TODO ack length?
    SubpacketEnum.BULK_SENSOR.value: 42,
}
for i in SubpacketIDs.get_list_of_sensor_IDs():
    PACKET_ID_TO_CONST_LENGTH[i] = 5

# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()


# # TODO Possibly deprecate this, since we have header helper that tracks header size
# # Map subpacket id to header size in bytes. Only includes types with CONSTANT lengths
# PACKET_ID_TO_HEADER_SIZE: Dict[int, int] = {
#     SubpacketEnum.STATUS_PING.value: 1,
#     SubpacketEnum.MESSAGE.value: 6,
#     SubpacketEnum.EVENT.value: 1,
#     SubpacketEnum.CONFIG.value: 1,
#     SubpacketEnum.GPS.value: 1,
#     SubpacketEnum.ACKNOWLEDGEMENT.value: 1,
#     SubpacketEnum.BULK_SENSOR.value: 1,
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
        data_length = header.total_length - header.header_length
        parsed_data: Dict[any, any] = self.parse_data(header.subpacket_id, data_unit, data_length)
        return parsed_data, header.total_length


    # Helper to convert byte to subpacket id as is in the SubpacketID enum, throws error otherwise
    def extract_subpacket_ID(self, byte: List):
        subpacket_id: int = int.from_bytes(byte, "big")
        # check that id is valid:
        if not SubpacketIDs.isSubpacketID(subpacket_id):
            # TODO Error log here?
            raise ValueError
        return SubpacketEnum(subpacket_id).value


    # general data parser interface
    def parse_data(self, type_id, byte_list, length):
        return self.packetTypeToParser[type_id](self, byte_list, length)

    # Header extractor helper
    def header(self, byte_list: List) -> Header:
        currByte = 0 # index for which byte is to be processed next. Collected in return as header size
        # Get ID
        subpacket_id: int = self.extract_subpacket_ID(byte_list[currByte])
        currByte += 1
        # Get timestamp
        # TODO REVIEW/CHANGE in type refactoring: how this is required to convert from List[bytes] to List[int]
        timestamp_int_list: List[int] = [int(x[0]) for x in byte_list[currByte: currByte + 4]]
        timestamp: int = self.fourtofloat(timestamp_int_list)
        currByte += 4
        # Get length
        if isPacketLengthConst(subpacket_id):
            length: int = PACKET_ID_TO_CONST_LENGTH[subpacket_id]
        else:
            length: int = int.from_bytes(byte_list[currByte], "big")
            currByte += 1
        return Header(subpacket_id, timestamp, currByte, length)

    ### General sensor data parsers

    def status_ping(self, byte_list, length):  # TODO
        converted = {0.0}  # STUB
        return converted

    def message(self, byte_list, length):  # TODO
        converted = {0.0}  # STUB
        return converted

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

        data[SubpacketEnum.TIME.value] = self.fourtoint(int_list[0:4])
        data[SubpacketEnum.CALCULATED_ALTITUDE.value] = self.fourtofloat(int_list[4:8])  # TODO Double check it is calculated barometer altitude with firmware
        data[SubpacketEnum.ACCELERATION_X.value] = self.fourtofloat(int_list[8:12])
        data[SubpacketEnum.ACCELERATION_Y.value] = self.fourtofloat(int_list[12:16])
        data[SubpacketEnum.ACCELERATION_Z.value] = self.fourtofloat(int_list[16:20])
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(int_list[20:24])
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(int_list[24:28])
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(int_list[28:32])
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(int_list[36:40])
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(int_list[32:36])
        data[SubpacketEnum.STATE.value] = int_list[40]
        return data


    # Dictionary of subpacket id - function to parse that data
    packetTypeToParser: Dict[int, Callable[[list, int], Any]] = {  # TODO review this type hint
        SubpacketEnum.STATUS_PING.value: status_ping,
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
