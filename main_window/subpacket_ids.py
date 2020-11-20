from enum import Enum

# Constants
MIN_SINGLE_SENSOR_ID: int = 0x10
MAX_SINGLE_SENSOR_ID: int = 0x2F


class SubpacketEnum(Enum):
    STATUS_PING = 0x00
    MESSAGE = 0x01
    EVENT = 0x02
    CONFIG = 0x03
    GPS = 0x04
    ORIENTATION = 0x06
    BULK_SENSOR = 0x30
    # Single Sensor:
    ACCELERATION_X = 0x10
    ACCELERATION_Y = 0x11
    ACCELERATION_Z = 0x12
    PRESSURE = 0x13
    BAROMETER_TEMPERATURE = 0x14
    TEMPERATURE = 0x15
    LATITUDE = 0x19
    LONGITUDE = 0x1A
    GPS_ALTITUDE = 0x1B
    CALCULATED_ALTITUDE = 0x1C
    STATE = 0x1D
    VOLTAGE = 0x1E
    GROUND_ALTITUDE = 0x1F
    TIME = 0x20
    ORIENTATION_1 = 0x21 # TODO Remove once dependencies can be resolved. Relates to https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
    ORIENTATION_2 = 0x22 # TODO Remove
    ORIENTATION_3 = 0x23 # TODO Remove
    ORIENTATION_4 = 0x24 # TODO Remove


def get_list_of_IDs():
    """

    :return:
    :rtype:
    """
    return [subpacket.value for subpacket in SubpacketEnum]


def get_list_of_names():
    """

    :return:
    :rtype:
    """
    return [subpacket.name for subpacket in SubpacketEnum]


def get_list_of_sensor_IDs():
    """

    :return:
    :rtype:
    """
    return [subpacket.value for subpacket in SubpacketEnum if isSingleSensorData(subpacket.value)]


def get_list_of_sensor_names():
    """

    :return:
    :rtype:
    """
    return [subpacket.name for subpacket in SubpacketEnum if isSingleSensorData(subpacket.value)]


def isSubpacketID(subpacket_id: int):
    """Check if it is a used ID

    :param subpacket_id:
    :type subpacket_id:
    :return:
    :rtype:
    """
    return subpacket_id in get_list_of_IDs()


def isSingleSensorData(subpacket_id):
    """Check if is singleSensor data

    :param subpacket_id:
    :type subpacket_id:
    :return:
    :rtype:
    """
    return MIN_SINGLE_SENSOR_ID <= subpacket_id <= MAX_SINGLE_SENSOR_ID
