from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from util.detail import LOGGER
from util.event_stats import Event
from .rocket_data import RocketData
from .data_entry_id import DataEntryIds

from main_window.nmea_gps_status import NMEAGpsStatus
import pynmea2
import io
import serial

CONNECTION_MESSAGE_READ_EVENT = Event('connection_message_read')

class NMEAThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, rocket_data: RocketData, serial_port, baudrate, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:=
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        
        # Setup Rocket Data
        self.rocket_data = rocket_data

        self.serial_port = serial_port
        self.baudrate = baudrate if baudrate else 9600
        self.is_thread_running = True

    def run(self):
        """TODO Description"""
        LOGGER.debug("NMEA thread started")

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
                self.new_gps_coordinate(status, float(latitude), float(longitude), float(altitude))

        except pynmea2.ParseError as e:
            status = "V"
            parse_error = e
            LOGGER.debug(f"Received GPS Data {status=} {parse_error=}")
            
    def new_gps_coordinate(self, status: NMEAGpsStatus, latitude: float, longitude: float, altitude: float):
        '''
        reupdate for ui
        '''
        connection_name = self.serial_port
        full_address = self.rocket_data.device_manager.connection_name_to_full_address(connection_name)
        if full_address is None:
            LOGGER.error(f"Could not find device for stage {full_address}!")
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
