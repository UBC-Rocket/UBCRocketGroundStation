import queue
from typing import Dict
from threading import RLock
from io import BytesIO, SEEK_END

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from util.detail import LOGGER
from connections.connection import ConnectionMessage
from .rocket_data import RocketData
from .packet_parser import PacketParser, DEVICE_TYPE
from .device_manager import DeviceManager


class ReadThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connection, rocket_data: RocketData, packet_parser: PacketParser, device_manager: DeviceManager, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:
        :param rocket_data:
        :type rocket_data:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.rocket_data = rocket_data

        self.packet_parser = packet_parser

        self.device_manager = device_manager

        self.dataQueue = queue.Queue()

        self.connection.registerCallback(self._newData)  # Must be done last to prevent race condition if IController
        # returns new data before ReadThread constructor is done

        self._shutdown_lock = RLock()
        self._is_shutting_down = False

    def _newData(self, connection_message: ConnectionMessage):
        """IConnection calls back to this function, this is where we get all our new data

        :param data:
        :type data:
        """
        self.dataQueue.put_nowait(connection_message)

    def run(self):
        """This thread loop waits for new data and processes it when available"""
        while True:

            connection_message = self.dataQueue.get(block=True, timeout=None)  # Block until something new
            self.dataQueue.task_done()

            if connection_message is None:  # Either received None or woken up for shutdown
                with self._shutdown_lock:
                    if self._is_shutting_down:
                        break
                    else:
                        continue

            hwid = connection_message.hwid
            connection = connection_message.connection
            data = connection_message.data

            byte_stream: BytesIO = BytesIO(data)

            # Get length of bytes (without using len(data) for decoupling)
            byte_stream.seek(0, SEEK_END)
            end = byte_stream.tell()
            byte_stream.seek(0)

            # Iterate over stream to extract subpackets where possible
            while byte_stream.tell() < end:
                try:
                    parsed_data: Dict[int, any] = self.packet_parser.extract(byte_stream)

                    if DEVICE_TYPE in parsed_data.keys():
                        self.device_manager.register_device(parsed_data[DEVICE_TYPE], hwid, connection)

                    device = self.device_manager.get_device(hwid)
                    if device is None:
                        LOGGER.warning(f"Received data from device which is not yet registered! (HWID={hwid})")
                        continue

                    self.rocket_data.addBundle(device, parsed_data)

                    # notify UI that new data is available to be displayed
                    self.sig_received.emit()
                except Exception as e:
                    LOGGER.exception("Error decoding new packet! %s", e)
                    # Just discard rest of data TODO Review policy on handling remaining data or problem packets. Consider data errors too
                    byte_stream.seek(0, SEEK_END)

        LOGGER.warning("Read thread shut down")

    def shutdown(self):
        with self._shutdown_lock:
            self._is_shutting_down = True
        self.dataQueue.put(None)  # Wake up thread
        self.wait()  # join thread
