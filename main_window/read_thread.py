import queue
from typing import Dict
from threading import RLock
from io import BytesIO, SEEK_END

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from main_window.data_entry_id import DataEntryIds
from util.detail import LOGGER
from util.event_stats import Event
from connections.connection import Connection, ConnectionMessage
from .rocket_data import RocketData
from .packet_parser import PacketParser
from .device_manager import DeviceManager, FullAddress

CONNECTION_MESSAGE_READ_EVENT = Event('connection_message_read')

class ReadThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connections: Dict[str, Connection], rocket_data: RocketData, packet_parser: PacketParser, device_manager: DeviceManager, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:
        :param rocket_data:
        :type rocket_data:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)

        self.connections = connections
        self.connection_to_name = {c: n for (n, c) in self.connections.items()}
        assert len(self.connections) == len(self.connection_to_name)  # Different if not one-to-one

        self.rocket_data = rocket_data

        self.packet_parser = packet_parser

        self.device_manager = device_manager

        self.dataQueue = queue.Queue()

        for connection in self.connections.values():
            connection.registerCallback(self._newData)
            # Must be done last to prevent race condition if IController
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
        LOGGER.debug("Read thread started")
        while True:

            connection_message = self.dataQueue.get(block=True, timeout=None)  # Block until something new
            self.dataQueue.task_done()

            if connection_message is None:  # Either received None or woken up for shutdown
                with self._shutdown_lock:
                    if self._is_shutting_down:
                        break
                    else:
                        continue

            connection = connection_message.connection
            full_address = FullAddress(connection_name=self.connection_to_name[connection],
                                       device_address=connection_message.device_address)
            data = connection_message.data

            byte_stream: BytesIO = BytesIO(data)

            # Get length of bytes (without using len(data) for decoupling)
            byte_stream.seek(0, SEEK_END)
            end = byte_stream.tell()
            byte_stream.seek(0)

            # Iterate over stream to extract subpackets where possible
            while byte_stream.tell() < end:
                try:
                    self.packet_parser.set_endianness(connection.isIntBigEndian(), connection.isFloatBigEndian())
                    parsed_data: Dict[DataEntryIds, any] = self.packet_parser.extract(byte_stream)

                    if DataEntryIds.DEVICE_TYPE in parsed_data and DataEntryIds.VERSION_ID in parsed_data:
                        self.device_manager.register_device(parsed_data[DataEntryIds.DEVICE_TYPE], parsed_data[DataEntryIds.VERSION_ID], full_address)
                    elif DataEntryIds.DEVICE_TYPE in parsed_data:
                        LOGGER.warning('Received DEVICE_TYPE but not VERSION_ID')
                    elif DataEntryIds.VERSION_ID in parsed_data:
                        LOGGER.warning('Received VERSION_ID but not DEVICE_TYPE')

                    self.rocket_data.add_bundle(full_address, parsed_data)

                    # notify UI that new data is available to be displayed
                    self.sig_received.emit()
                except Exception as e:
                    LOGGER.exception("Error decoding new packet! %s", e)
                    # Just discard rest of data TODO Review policy on handling remaining data or problem packets. Consider data errors too
                    byte_stream.seek(0, SEEK_END)

            CONNECTION_MESSAGE_READ_EVENT.increment()

        LOGGER.warning("Read thread shut down")

    def shutdown(self):
        with self._shutdown_lock:
            self._is_shutting_down = True
        self.dataQueue.put(None)  # Wake up thread
        self.wait()  # join thread
