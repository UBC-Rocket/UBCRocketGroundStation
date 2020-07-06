from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import queue

from RadioController import RadioController

class ReadThread(QtCore.QThread): #Updates GUI, therefore needs to be a QThread and use signals/slots
    sig_received = pyqtSignal()
    sig_print = pyqtSignal(str)

    def __init__(self, connection, rocketData, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.rocketData = rocketData

        self.radioController = RadioController(self.connection.isIntBigEndian(), self.connection.isFloatBigEndian())

        self.dataQueue = queue.Queue()

        self.errored = False

        self.connection.registerCallback(self._newData) # Must be done last to prevent race condition if IController
                                                        # returns new data before ReadThread constructor is done

    # IConnection calls back to this function, this is where we get all our new data
    def _newData(self, data):
        self.dataQueue.put_nowait(data)

    # This thread loop waits for new data and processes it when available
    def run(self):
        while True:

            data = self.dataQueue.get(block=True, timeout=None) # Block until something new
            self.dataQueue.task_done()

            byteList = [[x] for x in data] # sad that we still need this
            # loop that quickly runs through entire data list and extracts subpackets where possible
            while len(byteList) > 0:
                parsed_data: Dict[int, any] = {} # generally any is floats and ints
                length: int = 0
                try:
                    parsed_data, length = self.radioController.extract(byteList)
                    self.rocketData.addBundle(parsed_data)

                    #notify UI that new data is available to be displayed
                    self.sig_received.emit()
                except:
                    print("Error decoding new data!")

                del byteList[0:length]
