from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import queue

import RadioController

class ReadThread(QtCore.QThread): #Updates GUI, therefore needs to be a QThread and use signals/slots
    sig_received = pyqtSignal(object)
    sig_print = pyqtSignal(str)

    def __init__(self, connection, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.connection.registerCallback(self._newData)

        self.dataQueue = queue.Queue()

        self.errored = False

    # IConnection calls back to this function, this is where we get all our new data
    def _newData(self, data):
        self.dataQueue.put_nowait(data)

    # This thread loop waits for new data and processes it when available
    def run(self):
        self.running = True  # TODO Review purpose of this
        # Loop that attempts a message send and gets+parses data repeatedly
        while self.running:

            data = self.dataQueue.get(block=True, timeout=None) # Block until something new
            self.dataQueue.task_done()

            byteList = [[x] for x in data] # sad that we still need this
            # loop that quickly runs through entire data list and extracts subpackets where possible
            while len(byteList) > 0:
                parsed_data: Dict[int, any] = {} # generally any is floats and ints
                length: int = 0
                try:
                    parsed_data, length = RadioController.extract(byteList)
                except:
                    del byteList[0:1]
                    continue
                self.sig_received.emit(parsed_data)  # transmit it back to main, where function waits on this
                del byteList[0:length]


# TODO REVIEW/REMOVE this section once data types refactored

def _bytes_to_int(bytes):
    return int.from_bytes(bytes, byteorder='little', signed=False)  # TODO review this byteorder

def _bytes_to_byte(bytes):
    return bytes[0]

def _byte_list_to_bytearray(byte_list):
    ba = bytearray()
    for byte in byte_list:
        ba.append(int.from_bytes(byte, byteorder="big", signed='false'))  # TODO review this byteorder
    return ba

def _are_all(list, expected):
    for x in list:
        if x != expected:
            return False
    return True

def try_ascii_decode(bytes):
    try:
        bytes.decode("ascii")

    except:
        return False

    return True
