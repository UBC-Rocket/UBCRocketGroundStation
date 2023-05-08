import queue
from typing import Dict
from threading import RLock
from io import BytesIO, SEEK_END
from typing import Any

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from main_window.data_entry_id import DataEntryIds
from main_window.kiss_server import KissServer
from util.detail import LOGGER
from util.event_stats import Event
from connections.connection import Connection, ConnectionMessage
from .rocket_data import RocketData
from .packet_parser import PacketParser
from .device_manager import DeviceManager, FullAddress

CONNECTION_MESSAGE_READ_EVENT = Event('connection_message_read')
CALLSIGN = "KD2ZWJ"

class APRSThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connections: Dict[str, Connection], rocket_data: RocketData, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:=
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        
        # Create connections to names
        self.connections = connections
        self.connection_to_name = {c: n for (n, c) in self.connections.items()}
        assert len(self.connections) == len(self.connection_to_name)  # Different if not one-to-one
        
        # Create rocket stage to rocket names
        self.stage_to_name = {c.getStage(): n for (n, c) in self.connections.items()}

        self.rocket_data = rocket_data
        
        # Get kiss server address
        # All addresses for each connection should be the same.
        assert len({c.getKissAddress() for c in self.connections.values()}) == 1
        self.kissAddress = list(self.connections.values())[0].getKissAddress()
        
        # Start up the kiss server
        self.kissServer = KissServer(self.kissAddress)
        
        # Create APRS subscribers and parsers for each stage
        for c in self.connections.values():
            self.kissServer.add_subscriber(self.handle_aprs_packet)
            
    def handle_aprs_packet(self, packet: Dict[str, Any]):
        match packet:
            case {'from': CALLSIGN, 'ssid': stage, 'symbol': 'x'}:
                LOGGER.debug(f"Received GPS packet from {packet['from']}: == NO GPS LOCK ==")
            case {'from': CALLSIGN, 'ssid': stage, 'symbol': '~', 'latitude': latitude, 'longitude': longitude, 'altitude': altitude}:
                LOGGER.debug(f"Received GPS packet from {packet['from']}: {latitude=} {longitude=} {altitude=}")
                self.new_aprs_coordinate(int(stage), float(latitude), float(longitude), float(altitude))
            case {'from': CALLSIGN, 'ssid': stage, 'symbol': '~'}:
                LOGGER.error(f"Received GPS packet from {packet['from']} but no lat/long/alt data was found!")
            case {'from': CALLSIGN, 'ssid': stage, 'symbol': unknown_symbol}:
                LOGGER.warning(f"Unknown GPS Symbol {unknown_symbol} from packet {packet}")
                LOGGER.warning(f"This may or may not be a useful status symbol! Message one of the Groundstation devs ASAP!")
            case _:
                pass
            
    def new_aprs_coordinate(self, stage: int, latitude: float, longitude: float, altitude: float):
        # Check if stage actually exists
        if stage not in self.stage_to_name:
            raise ValueError(f"Received APRS packet for stage {stage} but no such stage exists!")

    def run(self):
        """TODO Description"""
        LOGGER.debug("APRS thread started")

        LOGGER.warning("APRS thread shut down")

    def shutdown(self):
        # idfk what this does
        self.wait()  # join thread
