import serial
import threading
import time

from ..connection import Connection, ConnectionMessage


class SerialConnection(Connection):

    def __init__(self, comPort: str, baudRate: int, kiss_address: str, stage: int = 1):
        self.device = serial.Serial(comPort, baudRate, timeout=1)
        self.kiss_address = kiss_address
        self.stage = stage
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
            # Need at least 1 byte for the size
            if len(self.buffer) < 1:
                return

            # Get the packet size
            packet_size = self.buffer[0]

            # Check if we have a complete packet
            if len(self.buffer) < packet_size:  # +1 for the size byte
                return  # Not enough data yet

            # Extract the packet data (excluding the size byte)
            data = self.buffer[1:packet_size]

            # Remove the processed packet from the buffer
            self.buffer = self.buffer[packet_size:]

            # Process the packet
            self._newData(bytes(data))

    def _newData(self, data):
        if self.callback:
            # Print each byte in base 10
            print("[!!!] Received data (base 10):", end=" ")
            for byte in data:
                print(byte, end=" ")
            print()
            # Since we don't have XBee device addresses, use the KISS address as the device address
            message = ConnectionMessage(
                device_address=self.kiss_address,
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

    def isIntBigEndian(self):
        return False

    def isFloatBigEndian(self):
        return False

    def getKissAddress(self) -> str:
        return self.kiss_address

    def getStage(self) -> int:
        return self.stage
