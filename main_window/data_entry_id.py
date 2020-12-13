from enum import Enum

# Constants
MIN_SINGLE_SENSOR_ID: int = 0x10
MAX_SINGLE_SENSOR_ID: int = 0x2F

class DataEntryIds(Enum):
    # PacketId/Data Types # TODO Move down to Data types once use as PacketId removed
    STATUS_PING = 0x00
    MESSAGE = 0x01
    EVENT = 0x02
    CONFIG = 0x03
    GPS = 0x04
    ORIENTATION = 0x06
    BULK_SENSOR = 0x30

    # Single Sensor: # TODO Review PacketParser.single_sensor depends on values matching packet IDs in spec
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

    # Data types
    IS_SIM = 0x25
    ROCKET_TYPE = 0x26
    VERSION_ID = 0x27

    # Sensors
    BAROMETER = 0x40
    #GPS = 'GPS' # TODO can just remove dups?
    #TEMPERATURE = 'TEMPERATURE'
    ACCELEROMETER = 0x41
    IMU = 0x42

    # Statuses
    NOMINAL = 0x43
    NONCRITICAL_FAILURE = 0x44
    CRITICAL_FAILURE = 0x45
    OVERALL_STATUS = 0x46

    # Misc items
    DROGUE_IGNITER_CONTINUITY = 0x47
    MAIN_IGNITER_CONTINUITY = 0x48
    FILE_OPEN_SUCCESS = 0x49

# TODO Remove along with commented funcs
def get_list_of_IDs():
    """

    :return:
    :rtype:
    """
    return [dataId.value for dataId in DataEntryIds]


# def get_list_of_names():
#     """
#
#     :return:
#     :rtype:
#     """
#     return [subpacket.name for subpacket in SubpacketEnum]

# TODO Review PacketParser.single_sensor depends on values matching packet IDs in spec
def get_list_of_sensor_IDs():
    """

    :return:
    :rtype:
    """
    return [dataId.value for dataId in DataEntryIds if is_single_sensor_data(dataId.value)]

# TODO Review PacketParser.single_sensor depends on values matching packet IDs in spec
def get_list_of_sensor_names():
    """

    :return:
    :rtype:
    """
    return [data_id.name for data_id in DataEntryIds if is_single_sensor_data(data_id.value)]


# def is_subpacket_id(data_id: int):
#     """Check if it is a used ID
#
#     :param data_id:
#     :type data_id:
#     :return:
#     :rtype:
#     """
#     return data_id in get_list_of_IDs()

# TODO Review PacketParser.single_sensor depends on values matching packet IDs in spec
def is_single_sensor_data(data_id: int):
    """Check if is singleSensor data

    :param data_id:
    :type data_id:
    :return:
    :rtype:
    """
    return MIN_SINGLE_SENSOR_ID <= int(data_id) <= MAX_SINGLE_SENSOR_ID
