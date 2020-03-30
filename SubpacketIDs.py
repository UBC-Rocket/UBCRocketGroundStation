from enum import Enum

#### Constants
MIN_SINGLE_SENSOR_ID: int = 0x10
MAX_SINGLE_SENSOR_ID: int = 0x2F

class SubpacketEnum(Enum):
    STATUS_PING = 0x00
    MESSAGE = 0x01
    EVENT = 0x02
    CONFIG = 0x03
    SINGLE_SENSOR = 0x04
    GPS = 0x05
    ACKNOWLEDGEMENT = 0x06
    BULK_SENSOR = 0x30
    ACCELERATION_X = 0x10
    ACCELERATION_Y = 0x11
    ACCELERATION_Z = 0x12
    PRESSURE = 0x13
    BAROMETER_TEMPERATURE = 0x14
    TEMPERATURE = 0x15
    YAW = 0x16
    ROLL = 0x17
    PITCH = 0x18
    LATITUDE = 0x19
    LONGITUDE = 0x20
    GPS_ALTITUDE = 0x21
    CALCULATED_ALTITUDE = 0x22
    STATE = 0x23
    VOLTAGE = 0x24
    GROUND_ALTITUDE = 0x25
    TIME = 0x26
    ORIENTATION_1 = 0x27
    ORIENTATION_2 = 0x28
    ORIENTATION_3 = 0x29

def get_list_of_IDs():
    return [subpacket.value for subpacket in SubpacketEnum]

def get_list_of_names():
    return [subpacket.name for subpacket in SubpacketEnum]

def get_list_of_sensor_IDs():
    return [subpacket.value for subpacket in SubpacketEnum if isSingleSensorData(subpacket.value)]

def get_list_of_sensor_names():
    return [subpacket.name for subpacket in SubpacketEnum if isSingleSensorData(subpacket.value)]

# Check if it is a used ID
def isSubpacketID(subpacket_id: int):
    return subpacket_id in get_list_of_IDs()

# Check if is singleSensor data
def isSingleSensorData(subpacket_id):
    return MIN_SINGLE_SENSOR_ID <= subpacket_id <= MAX_SINGLE_SENSOR_ID


# For reference, the sensor part mapping
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
