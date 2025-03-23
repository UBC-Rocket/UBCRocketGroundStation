from typing import Dict
from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from util.detail import LOGGER
from util.event_stats import Event
from .rocket_data import RocketData
from .data_entry_id import DataEntryIds
from connections.connection import Connection

from main_window.nmea_gps_status import NMEAGpsStatus
import pynmea2
import io
import serial

CONNECTION_MESSAGE_READ_EVENT = Event('connection_message_read')

class NMEAThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connections: Dict[str, Connection], rocket_data: RocketData, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:=
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        
        # Setup Rocket Data
        self.rocket_data = rocket_data

         # Create connections to names
        self.connections = connections
        self.connection_to_name = {c: n for (n, c) in self.connections.items()}
        assert len(self.connections) == len(self.connection_to_name)  # Different if not one-to-one
        
        # Create rocket stage to rocket names
        self.stage_to_connection_name = {c.getStage(): n for (n, c) in self.connections.items()}

        temp_connection = list(self.connections.values())[0]
        self.serial_port = temp_connection.getNMEASerialPort()
        self.baudrate = temp_connection.getNMEABaudRate()
        self.is_thread_running = True

    def run(self):
        """TODO Description"""
        LOGGER.debug("NMEA thread started")
        
        if self.serial_port and isinstance(self.serial_port, str):
             ser = serial.Serial(self.serial_port, self.baudrate, timeout=5.0)
             sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
             
             try:
                 while self.is_thread_running:
                     nmea_sentence = sio.readline()
                     if nmea_sentence.startswith("$GNRMC"):
                         self.handle_nmea_sentence(nmea_sentence)
 
             except serial.SerialException as e:
                 print('Failed to open serial port with error: {}'.format(e))

        LOGGER.warning("NMEA thread shut down")
            
    def handle_nmea_sentence(self, sentence: str): 
        try:
            msg = pynmea2.parse(sentence)
            status = msg.status

            if pynmea2.valid(status):
                latitude, longitude, altitude = msg.latitude, msg.longitude, msg.altitude
                
                LOGGER.debug(f"Received GPS Data {status=} {latitude=} {longitude=} {altitude=}")
                self.new_gps_coordinate(NMEAGpsStatus.GPS_VALID, float(latitude), float(longitude), float(altitude))

        except pynmea2.ParseError as e:
            status = "V"
            parsed_error = str(e)
            
            LOGGER.debug(f"Received GPS Data {status=} {parsed_error=}")
            self.new_gps_coordinate(NMEAGpsStatus.GPS_INVALID, None, None, None)
            
    def new_gps_coordinate(self, status: NMEAGpsStatus, latitude: float, longitude: float, altitude: float):
        stage: int = 1

        if status == NMEAGpsStatus.GPS_INVALID:
            self.rocket_data.add_bundle(full_address, {DataEntryIds.NMEA_STATUS: status})
            LOGGER.error(f"Received invalid NMEA data is invalid!")
            return

        connection_name = self.stage_to_connection_name[stage]
        full_address = self.rocket_data.device_manager.connection_name_to_full_address(connection_name)
        if full_address is None:
            LOGGER.error(f"Could not find device for stage {stage}!")
            return
        
        # Create new GPS Coordinate
        self.rocket_data.add_bundle(full_address, {
            DataEntryIds.NMEA_STATUS: status,
            DataEntryIds.NMEA_LATITUDE: latitude,
            DataEntryIds.NMEA_LONGITUDE: longitude,
            DataEntryIds.NMEA_ALTITUDE: altitude,
            DataEntryIds.NMEA_LAST_GPS_PING: datetime.now()
        })

    def shutdown(self):
        # idfk what this does
        self.is_thread_running = False
        self.wait()  # join thread
