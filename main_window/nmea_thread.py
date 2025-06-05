from typing import Dict, Optional
from datetime import datetime
import csv
import os

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
import traceback
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

        # Setup CSV logging
        self._setup_csv_logging()

    def _setup_csv_logging(self):
        """Initialize CSV logging with unique filename per instance"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # Create unique filename based on current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f'logs/nmea_log_{timestamp}.csv'

        # Create CSV file with header
        with open(self.csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'status', 'latitude', 'longitude', 'altitude'])

        LOGGER.info(f"NMEA CSV logging initialized: {self.csv_filename}")

    def _log_to_csv(self, status: NMEAGpsStatus, latitude: Optional[float] = None,
                   longitude: Optional[float] = None, altitude: Optional[float] = None):
        """Log GPS data to CSV file"""
        try:
            timestamp = datetime.now().isoformat()

            with open(self.csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    timestamp,
                    status.name if hasattr(status, 'name') else str(status),
                    latitude if latitude is not None else '',
                    longitude if longitude is not None else '',
                    altitude if altitude is not None else ''
                ])
        except Exception as e:
            LOGGER.error(f"Failed to log NMEA data to CSV: {e}")

    def run(self):
        """TODO Description"""
        LOGGER.debug("NMEA thread started")

        if self.serial_port and self.baudrate:
            ser = serial.Serial(self.serial_port,
                                self.baudrate,
                                timeout=5.0,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                xonxoff=False,
                                rtscts=True,
                                dsrdtr=True
                            )

            while self.is_thread_running:
                try:
                    try:
                        raw_bytes = ser.readline()
                    except serial.SerialException as e:
                        LOGGER.debug("Device error: {}".format(e))
                        print('Failed to open serial port with error: {}'.format(e))

                    if not raw_bytes:
                        continue

                    nmea_sentence = raw_bytes.decode('utf-8', errors='ignore').strip()

                    if not nmea_sentence:
                        continue

                    try:
                        msg = pynmea2.parse(nmea_sentence)
                    except pynmea2.ParseError as e:
                        status = "V"
                        parsed_error = str(e)

                        LOGGER.debug(f"Received GPS Data {status=} {parsed_error=}")
                        self.new_gps_coordinate(NMEAGpsStatus.GPS_INVALID)
                        continue

                    if msg.sentence_type == "GGA":
                        self.handle_nmea_sentence(msg)
                except Exception as e:
                    LOGGER.error(f"Error in NMEA thread: {e}")
                    traceback.print_exc()

            ser.close()
            LOGGER.warning("NMEA thread shut down")

    def handle_nmea_sentence(self, nmea_sentence):
        """Handle NMEA GGA sentence"""
        if hasattr(nmea_sentence, 'is_valid') and nmea_sentence.is_valid:
            latitude = nmea_sentence.latitude
            longitude = nmea_sentence.longitude
            altitude = nmea_sentence.altitude

            # Check if coordinates are valid (not None and not empty)
            if latitude is not None and longitude is not None and altitude is not None:
                try:
                    lat_float = float(latitude)
                    lon_float = float(longitude)
                    alt_float = float(altitude)

                    LOGGER.debug(f"Received GPS Data {latitude=} {longitude=} {altitude=}")
                    self.new_gps_coordinate(NMEAGpsStatus.GPS_VALID, lat_float, lon_float, alt_float)
                except (ValueError, TypeError) as e:
                    LOGGER.error(f"Failed to convert GPS coordinates to float: {e}")
                    self.new_gps_coordinate(NMEAGpsStatus.GPS_INVALID)
            else:
                LOGGER.warning("Received GPS Data with missing coordinates")
                self.new_gps_coordinate(NMEAGpsStatus.GPS_INVALID)
        else:
            LOGGER.warning(f"Received invalid GPS Data {nmea_sentence.sentence_type}")
            self.new_gps_coordinate(NMEAGpsStatus.GPS_INVALID)

    def new_gps_coordinate(self, status: NMEAGpsStatus, latitude: Optional[float] = None,
                          longitude: Optional[float] = None, altitude: Optional[float] = None):
        stage: int = 1

        connection_name = self.stage_to_connection_name[stage]
        full_address = self.rocket_data.device_manager.connection_name_to_full_address(connection_name)

        if full_address is None:
            LOGGER.error(f"Could not find device for stage {stage}!")
            return

        # Log to CSV file regardless of status
        self._log_to_csv(status, latitude, longitude, altitude)

        if status == NMEAGpsStatus.GPS_INVALID:
            self.rocket_data.add_bundle(full_address, {DataEntryIds.NMEA_STATUS: status})
            LOGGER.error(f"Received invalid NMEA data is invalid!")
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
