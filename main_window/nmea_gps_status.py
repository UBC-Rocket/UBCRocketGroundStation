from enum import Enum, auto
    
class NMEAGpsStatus(Enum):
    GPS_VALID = auto()
    GPS_INVALID = auto()