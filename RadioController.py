import struct
from typing import Dict, Any, Callable, Union, List

import RocketData
import SerialThread

#### Constants
MIN_SINGLE_SENSOR_ID: int = 0x10
MAX_SINGLE_SENSOR_ID: int = 0x2F

# map of packet ID to typename
PACKET_ID_TO_TYPE: Dict[int, str] = {
    0x00: "status_ping",
    0x01: "message",
    0x02: "event",
    0x03: "config",
    0x04: "single_sensor",
    0x05: "gps",
    0x06: "acknowledgement",
    0x30: "bulk_sensor",
}
# Add the single sensor id name pairs, using the dictionary of sensors in RocketData
# for name, id in zip(list(RocketData.nametochar.keys()), range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID)):
for name, subpacket_id in zip(list(RocketData.set_sensor_names), range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID)):
    PACKET_ID_TO_TYPE[subpacket_id] = name

# For reference, the added part will look like
#     0x10: "Acceleration X",
#     0x11: "Acceleration Y",
#     0x12: "Acceleration Z",
#     0x13: "Pressure",
#     0x14: "Barometer Temperature",
#     0x15: "Temperature",
#     0x16: "Yaw",
#     0x17: "Roll",
#     0x18: "Pitch",
#     0x19: "Latitude",
#     0x20: "Longitude",
#     0x21: "GPS Altitude",
#     0x22: "Calculated Altitude",
#     0x23: "State",
#     0x24: "Voltage",
#     0x25: "Ground Altitude",
#     0x26: "Time",
#     0x27: "Orientation 1",
#     0x28: "Orientation 2",
#     0x29: "Orientation 3"
# }

# Map subpacket id (int) to length (int) in bytes. Only includes types with CONSTANT lengths
PACKET_ID_TO_CONST_LENGTH: Dict[int, int] = {
    0x00: 4,
    0x02: 2,
    0x04: 25,
    0x05: 0000,  # TODO ack length?
    0x30: 42,
}
for i in range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID):
    PACKET_ID_TO_CONST_LENGTH[i] = 5


# Check if packet of given type has constant length
def isPacketLengthConst(subpacket_id):
    return subpacket_id in PACKET_ID_TO_CONST_LENGTH.keys()

# Check if is singleSensor data
def isSingleSensorData(subpacket_id: int):
    return subpacket_id >= MIN_SINGLE_SENSOR_ID or subpacket_id <= MAX_SINGLE_SENSOR_ID


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

    # # TODO Discuss ordering, to make it convenient to do this loop
    # i = 0
    # data["Time"] = RocketData.toint(byte_list[i:i+4])  # time
    # i = i + 4
    # floats = PACKET_ID_TO_TYPE.values
    # del floats["Time"] # remove time
    # del floats["State"] # remove state
    # for type in PACKET_ID_TO_TYPE.values: # iterate through float names
    #     data[type] = RocketData.fourtofloat(byte_list[i:i+4])
    #     i = i + 4

    # TODO Note how this is required to convert from List[bytes] to List[int]
    int_list: List[int] = [int(x[0]) for x in byte_list]

    # data["Time"] = RocketData.fourtoint(int_list[0:4])
    # # without hardcoding something else like id
    # data["Altitude"] = RocketData.fourtofloat(int_list[4:8])
    # data["Acceleration X"] = RocketData.fourtofloat(int_list[8:12])
    # data["Acceleration Y"] = RocketData.fourtofloat(int_list[12:16])
    # data["Acceleration Z"] = RocketData.fourtofloat(int_list[16:20])
    # data["Orientation 1"] = RocketData.fourtofloat(int_list[20:24])
    # data["Orientation 2"] = RocketData.fourtofloat(int_list[24:28])
    # data["Orientation 3"] = RocketData.fourtofloat(
    #     int_list[28:32])
    # data["Longitude"] = RocketData.fourtofloat(int_list[32:36])
    # data["Latitude"] = RocketData.fourtofloat(int_list[36:40])
    # data["State"] = int_list[40:41]

    # Alternative that only uses id to prevent bugs in future
    data[0x26] = RocketData.fourtoint(int_list[0:4])  # TODO Is there anyway of not having these as strings,
    # without hardcoding something else like id
    data[0x22] = RocketData.fourtofloat(int_list[4:8]) # Double check it is calculated barometer altitude with firmware
    data[0x10] = RocketData.fourtofloat(int_list[8:12])
    data[0x11] = RocketData.fourtofloat(int_list[12:16])
    data[0x12] = RocketData.fourtofloat(int_list[16:20])
    data[0x27] = RocketData.fourtofloat(int_list[20:24])
    data[0x28] = RocketData.fourtofloat(int_list[24:28])
    data[0x29] = RocketData.fourtofloat(
        int_list[28:32])  # TODO Remember to use these in calculating quaternion
    data[0x19] = RocketData.fourtofloat(int_list[36:40])
    data[0x20] = RocketData.fourtofloat(int_list[32:36]) # TODO Check that order is correct for long/lat
    data[0x23] = int_list[40]
    print(data)  # TODO remove
    return data


# Dictionary of subpacket id - function to parse that data
packetTypeToParser: Dict[int, Callable[[list, int], Any]] = { # TODO review this type hint
    # 0x00: status_ping,
    # 0x01: message,
    # 0x02: event,
    # 0x03: config,
    # 0x04: single_sensor,
    # 0x05: gps,
    # 0x06: acknowledgement, # TODO Uncomment when rest complete
    0x30: bulk_sensor,
}
