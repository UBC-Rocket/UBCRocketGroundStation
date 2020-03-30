from typing import Dict, Any, Callable, Union, List

import RocketData
import SubpacketIDs
from SubpacketIDs import SubpacketEnum

# # map of packet ID to typename
# PACKET_ID_TO_TYPE: Dict[int, str] = {
#     0x00: "status_ping",
#     0x01: "message",
#     0x02: "event",
#     0x03: "config",
#     0x04: "single_sensor",
#     0x05: "gps",
#     0x06: "acknowledgement",
#     0x30: "bulk_sensor",
# }
# # Add the single sensor id name pairs, using the dictionary of sensors in RocketData
# # for name, id in zip(list(RocketData.nametochar.keys()), range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID)):
# for name, subpacket_id in zip(list(RocketData.set_sensor_names), range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID)):
#     PACKET_ID_TO_TYPE[subpacket_id] = name


# Map subpacket id (int) to length (int) in bytes. Only includes types with CONSTANT lengths
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    0x00: 4,
    0x02: 2,
    0x04: 25,
    0x05: 0000,  # TODO ack length?
    0x30: 42,
}
for i in SubpacketIDs.get_list_of_sensor_IDs():
    PACKET_ID_TO_CONST_LENGTH[i] = 5


# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()


# Return dict of subpacket id, length of subpacket in byte_list, subpacket typename, data_unit
# Current implementation strips off subpacket id + length (if included), returning dictionary of id and data length
def extract_subpacket(byte_list: List):
    subpacket_id: int = int.from_bytes(byte_list[0], "big")
    length: int = 0
    # check that id is valid:
    if subpacket_id not in PACKET_ID_TO_TYPE:
        raise ValueError
    if isPacketLengthConst(subpacket_id):
        length = PACKET_ID_TO_CONST_LENGTH[int.from_bytes(byte_list[0], "big")]
        data_unit = byte_list[1:length]
        del byte_list[0:1]
        length = length - 1 #TODO Fix this bad code somehow
    else:
        length = int.from_bytes(byte_list[1], "big")
        data_unit = byte_list[2:length]
        del byte_list[0:2]
        length = length - 2 #TODO Fix this bad code somehow
    parsed_subpacket: Dict[str, Union[int, str]] = {'id': subpacket_id, 'length': length}
    return parsed_subpacket


# general data parser interface
def parse_data(type_id, byte_list, length):
    return packetTypeToParser[type_id](byte_list, length)


def status_ping(byte_list, length):  # TODO
    converted = 0.0
    return converted

def message(byte_list, length):  # TODO
    converted = 0.0  # STUB
    return converted

def event(byte_list, length):  # TODO
    converted = 0.0  # STUB
    return converted

def config(byte_list, length):  # TODO
    converted = 0.0  # STUB
    return converted

def single_sensor(byte_list, length):  # TODO
    converted = 0.0  # STUB
    return converted

def gps(byte_list, length):  # TODO
    converted = 0.0  # STUB
    return converted

# def acknowledgement(byte_list, length):  # TODO ?
#     converted = 0.0  # STUB
#     return converted

def bulk_sensor(byte_list: List, length: int):
    data: Dict[str: Union[float, int]] = {}

    # TODO Note how this is required to convert from List[bytes] to List[int]
    int_list: List[int] = [int(x[0]) for x in byte_list]

    # Alternative that only uses id to prevent bugs in future
    data[SubpacketEnum.TIME.value] = RocketData.fourtoint(int_list[0:4])
    # without hardcoding something else like id
    data[SubpacketEnum.CALCULATED_ALTITUDE.value] = RocketData.fourtofloat(int_list[4:8]) # Double check it is calculated barometer altitude with firmware
    data[SubpacketEnum.ACCELERATION_X.value] = RocketData.fourtofloat(int_list[8:12])
    data[SubpacketEnum.ACCELERATION_Y.value] = RocketData.fourtofloat(int_list[12:16])
    data[SubpacketEnum.ACCELERATION_Z.value] = RocketData.fourtofloat(int_list[16:20])
    data[SubpacketEnum.ORIENTATION_1.value] = RocketData.fourtofloat(int_list[20:24])
    data[SubpacketEnum.ORIENTATION_2.value] = RocketData.fourtofloat(int_list[24:28])
    data[SubpacketEnum.ORIENTATION_3.value] = RocketData.fourtofloat(int_list[28:32])  # TODO Remember to use these in calculating quaternion
    data[SubpacketEnum.LONGITUDE.value] = RocketData.fourtofloat(int_list[36:40])
    data[SubpacketEnum.LATITUDE.value] = RocketData.fourtofloat(int_list[32:36]) # TODO Check that order is correct for long/lat
    data[SubpacketEnum.STATE.value] = int_list[40]
    print(data)  # TODO remove
    return data


# Dictionary of subpacket id - function to parse that data
packetTypeToParser: Dict[int, Callable[[list, int], Any]] = { # TODO review this type hint
    # SubpacketEnum.STATUS_PING.value: status_ping,
    # SubpacketEnum.MESSAGE.value: message,
    # SubpacketEnum.EVENT.value: event,
    # SubpacketEnum.CONFIG.value: config,
    # SubpacketEnum.SINGLE_SENSOR.value: single_sensor,
    # SubpacketEnum.GPS.value: gps,
    # SubpacketEnum.ACKNOWLEDGEMENT.value: acknowledgement, # TODO Uncomment when rest complete
    SubpacketEnum.BULK_SENSOR.value: bulk_sensor,
}
