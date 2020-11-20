import queue
from typing import Dict
from threading import RLock
from io import BytesIO, SEEK_END

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from .packet_parser import PacketParser
from util.detail import LOGGER


class ReadThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connection, rocket_data, parent=None) -> None:
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

        self.packet_parser = PacketParser(self.connection.isIntBigEndian(), self.connection.isFloatBigEndian())

        self.dataQueue = queue.Queue()

        self.connection.registerCallback(self._newData)  # Must be done last to prevent race condition if IController
        # returns new data before ReadThread constructor is done

        self._shutdown_lock = RLock()
        self._is_shutting_down = False

    def _newData(self, data):
        """IConnection calls back to this function, this is where we get all our new data

        :param data:
        :type data:
        """
        self.dataQueue.put_nowait(data)

    def run(self):
        """This thread loop waits for new data and processes it when available"""
        while True:

            data = self.dataQueue.get(block=True, timeout=None)  # Block until something new
            self.dataQueue.task_done()

            if data is None:  # Either received None or woken up for shutdown
                with self._shutdown_lock:
                    if self._is_shutting_down:
                        break
                    else:
                        continue

            byte_stream: BytesIO = BytesIO(data)
            curr_offset = 0

            # Get length of bytes (without using len(data) for decoupling)
            byte_stream.seek(0, SEEK_END)
            end = byte_stream.tell()
            byte_stream.seek(0)

            # Iterate over stream to extract subpackets where possible
            while byte_stream.tell() < end:
                try:
                    parsed_data: Dict[int, any] = self.packet_parser.extract(byte_stream)
                    self.rocket_data.addBundle(parsed_data)
                    curr_offset = byte_stream.tell()

                    # notify UI that new data is available to be displayed
                    self.sig_received.emit()
                except Exception as e:
                    LOGGER.exception("Error decoding new data!")  # Automatically grabs and prints exception info
                    byte_stream.seek(curr_offset+1)

        LOGGER.warning("Read thread shut down")

    def shutdown(self):
        with self._shutdown_lock:
            self._is_shutting_down = True
        self.dataQueue.put(None)  # Wake up thread
        self.wait()  # join thread
