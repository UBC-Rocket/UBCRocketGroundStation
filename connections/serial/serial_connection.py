import serial
import threading
import time
from typing import Optional

from ..connection import Connection, ConnectionMessage


class SerialConnection(Connection):

    def __init__(
            self,
            comPort: str,
            baudRate: int,
            stage: int = 1,
            nmea_serial_port: Optional[str] = None,
            nmea_baud_rate: Optional[int] = None
        ):
        self.device = serial.Serial(comPort, baudRate, timeout=1)
        self.stage = stage
        self.nmea_serial_port = nmea_serial_port
        self.nmea_baud_rate = nmea_baud_rate

        self.callback = None
        self.running = True
        self.buffer = bytearray()

        # Start a thread to read from the serial port
        self.read_thread = threading.Thread(target=self._read_serial)
        self.read_thread.daemon = True
        self.read_thread.start()

    def _read_serial(self):
        """Thread function to continuously read from the serial port"""
        while self.running:
            try:
                # Read available data and add to buffer
                if self.device.in_waiting > 0:
                    new_data = self.device.read(self.device.in_waiting)
                    self.buffer.extend(new_data)
                    # Print each byte in base 10
                    print("Received new_data (base 10):", end=" ")
                    for byte in new_data:
                        print(byte, end=" ")
                    print()

                # Process complete packets from the buffer
                self._process_buffer()

                # Small delay to prevent CPU hogging
                time.sleep(0.01)
            except Exception as e:
                print(f"Serial read error: {e}")

    def _process_buffer(self):
        """Process complete packets from the buffer"""
        while len(self.buffer) > 0:
            # # Need at least 1 byte for the size
            # if len(self.buffer) < 1:
            #     return

            # # Get the packet size
            # packet_size = self.buffer[0]

            # # Check if we have a complete packet
            # if len(self.buffer) < packet_size:
            #     return  # Not enough data yet

            # # Extract the packet data (excluding the size byte)
            # data = self.buffer[1:packet_size]

            # # Remove the processed packet from the buffer
            # self.buffer = self.buffer[packet_size:]

            # # Process the packet
            # self._newData(bytes(data))

            #######################################
            # Okay this is a giga-hacky way to get the rocket to work with the new packet format.
            # Just for sunburst, the packet was shortened from 44 bytes down to 10 bytes.

            # This was the original packet:
            # [size: 1 byte] [packet_id: 1 byte] [time: 4 bytes] [altitude: 4 bytes] [accelerometer: 12 bytes] [imu: 12 bytes] [gps: 8 bytes] [state: 2 bytes]

            # This is the new packet:
            # [time: 4 bytes] [altitude: 4 bytes] [state: 2 bytes]

            # As a quick hack, we are just going to translate the new packet to the old packet.
            # This just makes it so that the packet parser can still work.

            # TODO: Remove this once the rocket is updated to use the new packet format.

            # Need at least 10 bytes to process the packet
            if len(self.buffer) < 10:
                return

            # Get the packet data
            data = self.buffer[:10]

            # Translate the new packet to the old packet
            old_data = bytearray([0x30]) + data[0:4] + data[4:8] + bytearray(12 + 12 + 8) + data[8:10]

            # Remove the processed packet from the buffer
            self.buffer = self.buffer[10:]

            # Process the packet
            self._newData(bytes(old_data))

            #######################################

    def _newData(self, data):
        if self.callback:
            # Print each byte in base 10
            print("[!!!] Received data (base 10):", end=" ")
            for byte in data:
                print(byte, end=" ")
            print()
            message = ConnectionMessage(
                device_address=None,
                connection=self,
                data=data)

            self.callback(message)

    def registerCallback(self, fn):
        self.callback = fn

    def send(self, device_address, data):
        packet_size = len(data)
        size_byte = packet_size.to_bytes(1, byteorder='little')
        self.device.write(size_byte + data)

    def broadcast(self, data):
        self.send(None, data)

    def shutdown(self):
        self.running = False
        if self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        self.device.close()

    def getDeviceAddress(self) -> Optional[str]:
        return None

    def isIntBigEndian(self):
        return False

    def isFloatBigEndian(self):
        return False

    def getStage(self) -> int:
        return self.stage

    def getKissAddress(self) -> Optional[str]:
        return self.kiss_address

    def getNMEASerialPort(self) -> Optional[str]:
        return self.nmea_serial_port

    def getNMEABaudRate(self) -> Optional[int]:
        return self.nmea_baud_rate
