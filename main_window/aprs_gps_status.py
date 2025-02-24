from enum import Enum, auto
    
class AprsGpsStatus(Enum):
    GPS_OFFLINE = auto()
    GPS_NO_LOCK = auto()
    GPS_LOCKED = auto()
    GPS_LOST_LOCK = auto()
    GPS_ERROR = auto()
    GPS_UNKNOWN = auto()
