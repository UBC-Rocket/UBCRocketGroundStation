from typing import Optional, Callable, List, Dict, Any
from util.detail import LOGGER
from main_window.kiss_server import KissServer

CALLSIGN = "KD2ZWJ-2"

class APRSParser:
    def __init__(self, kiss_server: Optional[KissServer] = None):
        # Setup GPS Coordinates
        self.latitude = 0
        self.longitude = 0
        self.altitude = 0
        
        # If kiss server is passed, add the kiss subscriber
        if kiss_server:
            kiss_server.add_subscriber(self.kiss_subscriber)
    
    def kiss_subscriber(self, packet):
        match packet:
            case {'from': CALLSIGN, 'symbol': 'x'}:
                LOGGER.debug(f"Received GPS packet: == NO GPS LOCK ==")
            case {'from': CALLSIGN, 'symbol': '~', 'latitude': latitude, 'longitude': longitude, 'altitude': altitude}:
                LOGGER.debug(f"Received GPS packet: {latitude=} {longitude=} {altitude=}")
                self.latitude = latitude
                self.longitude = longitude
                self.altitude = altitude
            case {'from': CALLSIGN, 'symbol': unknown_symbol}:
                LOGGER.error(f"Unknown GPS Symbol {unknown_symbol} from packet {packet}")
            case _:
                pass
        
    def get_gps_coordinates(self):
        return self.latitude, self.longitude, self.altitude
