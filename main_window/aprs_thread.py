from typing import Dict, Any
from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from main_window.kiss_server import KissServer
from main_window.aprs_gps_status import AprsGpsStatus
from util.detail import LOGGER
from util.event_stats import Event
from connections.connection import Connection
from .rocket_data import RocketData
from .data_entry_id import DataEntryIds

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
        self.stage_to_connection_name = {c.getStage(): n for (n, c) in self.connections.items()}

        # Setup Rocket Data
        self.rocket_data = rocket_data
        
        # Get kiss server address
        # All addresses for each connection should be the same.
        assert len({c.getKissAddress() for c in self.connections.values()}) == 1
        self.kiss_address = list(self.connections.values())[0].getKissAddress()
        
        # Start up the kiss server
        self.kiss_server = KissServer(self.kiss_address)
        
        # Create APRS subscribers and parsers for each stage
        for c in self.connections.values():
            self.kiss_server.add_subscriber(self.handle_aprs_packet)
            
    def handle_aprs_packet(self, packet: Dict[str, Any]):
        if "from" in packet and packet["from"] != CALLSIGN:
            LOGGER.warning(f"Received packet from {packet['from']} but expected {CALLSIGN}")
            
        match packet:
            # Garbled aprs packet with symbol x - No GPS Lock (and hasn't ever gotten one)
            case {'ssid': stage, 'symbol': 'x'}:
                self.update_gps_status(int(stage), AprsGpsStatus.GPS_NO_LOCK)
                LOGGER.debug(f"Received GPS packet from {packet['from']} (Stage: {stage}): == NO GPS LOCK ==")
        
            # Fully formed aprs packet with symbol ~ and comment * - GPS Locked and has lat/long/alt data
            case {'ssid': stage, 'comment': '*', 'latitude': latitude, 'longitude': longitude, 'altitude': altitude}:
                LOGGER.debug(f"Received GPS packet from {packet['from']} (Stage: {stage}): {latitude=} {longitude=} {altitude=}")
                self.new_gps_coordinate(int(stage), float(latitude), float(longitude), float(altitude))
                
            # Catch case where sent fully formed aprs packet with symbol ~ and comment *, but no lat/long/alt data
            case {'ssid': stage, 'comment': '*'}:
                self.update_gps_status(int(stage), AprsGpsStatus.GPS_ERROR)
                LOGGER.error(f"Received GPS packet from {packet['from']} (Stage: {stage}) but no lat/long/alt data was found!")
                
            # Garbled aprs packet with symbol ~ and comment - - GPS Lock Lost (but had one before)
            case {'ssid': stage, 'comment': '-'}:
                self.update_gps_status(int(stage), AprsGpsStatus.GPS_LOST_LOCK)
                LOGGER.debug(f"Received GPS packet from {packet['from']} (Stage: {stage}): == GPS LOCK LOST ==")
                
            # Handle unknown comment when symbol is ~
            case {'ssid': stage, 'comment': unknown_comment}:
                self.update_gps_status(int(stage), AprsGpsStatus.GPS_ERROR)
                LOGGER.error(f"Unknown GPS Comment {unknown_comment} from packet {packet}!")
                LOGGER.error(f"This may or may not be a useful status symbol! Message one of the Groundstation devs ASAP!")
                
            # Handle unknown symbol
            case {'ssid': stage, 'symbol': unknown_symbol}:
                self.update_gps_status(int(stage), AprsGpsStatus.GPS_ERROR)
                LOGGER.error(f"Unknown GPS Symbol {unknown_symbol} from packet {packet}!")
                LOGGER.error(f"This may or may not be a useful status symbol! Message one of the Groundstation devs ASAP!")
              
            # Dont handle packets from any other callsigns  
            case _:
                pass
            
    def new_gps_coordinate(self, stage: int, latitude: float, longitude: float, altitude: float):
        # Check if stage actually exists
        if stage not in self.stage_to_connection_name:
            self.update_gps_status(stage, AprsGpsStatus.GPS_ERROR)
            LOGGER.error(f"Received APRS packet for stage {stage} but no such stage exists!")
            return
        
        # Get Full Address from Stage ID
        connection_name = self.stage_to_connection_name[stage]
        full_address = self.rocket_data.device_manager.connection_name_to_full_address(connection_name)
        if full_address is None:
            LOGGER.error(f"Could not find device for stage {stage}!")
            return
        
        # Create new GPS Coordinate
        self.rocket_data.add_bundle(full_address, {
            DataEntryIds.APRS_STATUS: AprsGpsStatus.GPS_LOCKED,
            DataEntryIds.APRS_LATITUDE: latitude,
            DataEntryIds.APRS_LONGITUDE: longitude,
            DataEntryIds.APRS_ALTITUDE: altitude,
            DataEntryIds.APRS_LAST_GPS_PING: datetime.now()
        })
        
    def update_gps_status(self, stage: int, status: AprsGpsStatus):
        # Check if stage actually exists
        if stage not in self.stage_to_connection_name:
            self.update_gps_status(stage, AprsGpsStatus.GPS_ERROR)
            LOGGER.error(f"Received APRS packet for stage {stage} but no such stage exists!")
            return
        
        # Get Full Address from Stage ID
        connection_name = self.stage_to_connection_name[stage]
        full_address = self.rocket_data.device_manager.connection_name_to_full_address(connection_name)
        if full_address is None:
            LOGGER.error(f"Could not find device for stage {stage}!")
            return
        
        self.rocket_data.add_bundle(full_address, {DataEntryIds.APRS_STATUS: status})

    def run(self):
        """TODO Description"""
        LOGGER.debug("APRS thread started")

        # Start accepting KISS Packets
        self.kiss_server.run()

        LOGGER.warning("APRS thread shut down")

    def shutdown(self):
        # idfk what this does
        self.wait()  # join thread
