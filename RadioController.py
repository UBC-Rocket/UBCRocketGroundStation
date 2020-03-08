# List of sensor ids to names for reference
# PACKET_ID_SENSOR_TO_NAME = {
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
#     0x26: "Time"
# }
# chartosensorname = {}
# for x in sensornametochar:
#     chartosensorname[sensornametochar[x]] = x

# Constants
from typing import Dict, Any, Callable

import RocketData

MIN_SINGLE_SENSOR_ID = 0x10
MAX_SINGLE_SENSOR_ID = 0x2F

# map of packet ID to typename
PACKET_ID_TO_TYPE = {
    0x00: "status_ping",
    0x01: "message",
    0x02: "event",
    0x03: "config",
    0x04: "single_sensor",
    0x05: "gps",
    0x06: "acknowledgement",
    0x10: "Acceleration X",
    0x11: "Acceleration Y",
    0x12: "Acceleration Z",
    0x13: "Pressure",
    0x14: "Barometer Temperature",
    0x15: "Temperature",
    0x16: "Yaw",
    0x17: "Roll",
    0x18: "Pitch",
    0x19: "Latitude",
    0x20: "Longitude",
    0x21: "GPS Altitude",
    0x22: "Calculated Altitude",
    0x23: "State",
    0x24: "Voltage",
    0x25: "Ground Altitude",
    0x26: "Time",
    ### 0x27 - 0x2F are free
    0x30: "bulk_sensor",
}
# for i in range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID):
#     PACKET_ID_TO_TYPE[i] = "single_sensor"

# Map subpacket id (int) to length (int) in bytes. Only includes types with CONSTANT lengths
PACKET_ID_TO_CONST_LENGTH = {
    0x00: 4,
    0x02: 2,
    0x04: 25,
    0x05: 0000,  ## TODO ack length
    0x30: 42,
}
for i in range(MIN_SINGLE_SENSOR_ID, MAX_SINGLE_SENSOR_ID):
    PACKET_ID_TO_CONST_LENGTH[i] = 5

# Check if packet of given type has variable length
def isPacketLengthVariable(packet_id):
    return packet_id in PACKET_ID_TO_CONST_LENGTH.keys()


# Check if is singleSensor data
def isSingleSensorData(packet_id):
    return packet_id >= MIN_SINGLE_SENSOR_ID or packet_id <= MAX_SINGLE_SENSOR_ID


# Return dict with id, length, typename, data_unit
def extract_subpacket(byte_list):
    packet_id = int.from_bytes(byte_list[0], "big")
    length = 0
    data_unit = b""
    # check that id is valid:
    if packet_id not in PACKET_ID_TO_TYPE:
        raise ValueError
    if isPacketLengthVariable(packet_id):
        length = int.from_bytes(byte_list[1], "big")
        data_unit = byte_list[2:length]
    else:
        length = PACKET_ID_TO_CONST_LENGTH[byte_list[0]]
        data_unit = byte_list[1:length]
    type_id = PACKET_ID_TO_TYPE[packet_id]
    parsed_subpacket = {
        packet_id,  # id in raw byte format
        length,  # length
        type_id,  # type
        data_unit,  # data unit
    }
    return parsed_subpacket


# general data parser interface
def parse_data(type_id, byte_list, length):
    packetTypeToHandler[type_id](byte_list)


def status_ping(byte_list, length): #TODO
    converted = 0.0
    return converted


def message(byte_list, length): # TODO
    converted = 0.0 # STUB
    return converted


def event(byte_list, length): # TODO
    converted = 0.0 # STUB
    return converted


def config(byte_list, length): # TODO
    converted = 0.0 # STUB
    return converted


def gps(byte_list, length): # TODO
    converted = 0.0 # STUB
    return converted


def single_sensor(byte_list, length): # TODO
    converted = 0.0 # STUB
    return converted


def bulk_sensor(byte_list, length):
    time = RocketData.toint(byte_list[0:4])
    altitude = RocketData.fourtofloat(byte_list[4:8])
    accelx = RocketData.fourtofloat(byte_list[8:12])
    accely = RocketData.fourtofloat(byte_list[12:16])
    accelz = RocketData.fourtofloat(byte_list[16:20])
    orient1 = RocketData.fourtofloat(byte_list[20:24])
    orient2 = RocketData.fourtofloat(byte_list[24:28])
    orient3 = RocketData.fourtofloat(byte_list[28:32])
    gps1 = RocketData.fourtofloat(byte_list[32:36])
    gps2 = RocketData.fourtofloat(byte_list[36:30])
    state = byte_list[40:41]
    data = {
        time,
        altitude,
        accelx,
        accely,
        accelz,
        orient1,
        orient2,
        orient3,
        gps1,
        gps2,
        state,
    }
    return data


########

packetTypeToHandler: Dict[str, Callable[[Any, Any], float]] = {
    # "statusPing": RadioController.status_ping,
    # "message": RadioController.message,
    # "event": RadioController.event,
    # "config": RadioController.config,
    # "singleSensor": RadioController.single_sensor,
    # "gps": RadioController.gps,
    "bulk_sensor": bulk_sensor,
}
