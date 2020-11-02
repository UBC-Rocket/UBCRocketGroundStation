import queue
from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from .radio_controller import RadioController
from util.detail import LOGGER


class ReadThread(QtCore.QThread):
    sig_received = pyqtSignal()
    sig_print = pyqtSignal(str)

    def __init__(self, connection, rocketData, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:
        :param rocketData:
        :type rocketData:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.rocketData = rocketData

        self.radioController = RadioController(self.connection.isIntBigEndian(), self.connection.isFloatBigEndian())

        self.dataQueue = queue.Queue()

        self.errored = False

        self.connection.registerCallback(self._newData)  # Must be done last to prevent race condition if IController
        # returns new data before ReadThread constructor is done

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

            # Convert from immutable bytearray to List[int]
            byte_list = list(data)  # list of ints ranging from 0 - 255. Equivalent to doing [x for x in data]

            # loop that quickly runs through entire data list and extracts subpackets where possible
            while len(byte_list) > 0:
                parsed_data: Dict[int, any] = {}  # generally any is floats and ints
                length: int = 0
                try:
                    parsed_data, length = self.radioController.extract(byte_list)
                    self.rocketData.addBundle(parsed_data)

                    # notify UI that new data is available to be displayed
                    self.sig_received.emit()
                except Exception as e:
                    LOGGER.exception("Error decoding new data!") # Automatically grabs and prints exception info

                del byte_list[0:length]
