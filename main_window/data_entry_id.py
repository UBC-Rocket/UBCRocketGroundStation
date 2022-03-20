from enum import Enum, auto

class DataEntryIds(Enum):
    # Single Sensor:
    ACCELERATION_X = auto()
    ACCELERATION_Y = auto()
    ACCELERATION_Z = auto()
    PRESSURE = auto()
    BAROMETER_TEMPERATURE = auto()
    TEMPERATURE = auto()
    LATITUDE = auto()
    LONGITUDE = auto()
    GPS_ALTITUDE = auto()
    CALCULATED_ALTITUDE = auto()
    STATE = auto()
    VOLTAGE = auto()
    GROUND_ALTITUDE = auto()
    TIME = auto()
    ORIENTATION_1 = auto() # TODO Remove once dependencies can be resolved. Relates to https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
    ORIENTATION_2 = auto() # TODO Remove
    ORIENTATION_3 = auto() # TODO Remove
    ORIENTATION_4 = auto() # TODO Remove

    # Data types
    MESSAGE = auto()
    EVENT = auto()
    CONFIG = auto()
    ORIENTATION = auto()
    BULK_SENSOR = auto()
    IS_SIM = auto()
    DEVICE_TYPE = auto()
    VERSION_ID = auto()

    # Sensors
    GPS = auto()
    BAROMETER = auto()
    ACCELEROMETER = auto()
    IMU = auto()

    # Status
    OVERALL_STATUS = auto()
    DROGUE_IGNITER_CONTINUITY = auto()
    MAIN_IGNITER_CONTINUITY = auto()
    FILE_OPEN_SUCCESS = auto()


class DataEntryValues(Enum):
    STATUS_NOMINAL = auto()
    STATUS_NONCRITICAL_FAILURE = auto()
    STATUS_CRITICAL_FAILURE = auto()

    STATE_STANDBY = auto()
    STATE_ARMED = auto()
    STATE_ASCENT_TO_APOGEE = auto()
    STATE_POWERED_ASCENT = auto()
    STATE_PRE_AIR_START_COAST_TIMED = auto()
    STATE_MACH_LOCK = auto()
    STATE_PRESSURE_DELAY = auto()
    STATE_DROGUE_DESCENT = auto()
    STATE_MAIN_DESCENT = auto()
    STATE_LANDED = auto()
    STATE_WINTER_CONTINGENCY = auto()
    # STATE_ASCENT = auto() # TODO Remove in this PR
    # STATE_INITIAL_DESCENT = auto() # TODO Remove in this PR
    # STATE_FINAL_DESCENT = auto() # TODO Remove in this PR

    # TODO Add other info stored

    # Events
    EVENT_IGNITOR_FIRED = auto()
    EVENT_LOW_VOLTAGE = auto()
