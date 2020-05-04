import time
from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from digi.xbee.exception import TimeoutException, XBeeException
import queue

import RadioController
import RocketData

# TODO change this section with new Radio protocol comm refactoring
COM_ID = {  # TODO ASK Are we going to continue to send single characters according to user commands? If yes, then why not provide drop down/multiple select??? AND This should not be here anyway, it relates to communication protocl -> RadioController
    "arm": 'r',
    "cameras on": 'C',
    "cameras off": 'O',
    "halo": 'H',
    "satcom": 's',
    "reset": 'R',
    "status": 'S',
    "main": 'm',
    "drogue": 'd',
    "ping": 'p'
}
#
# COM_NAME = {}
# for x in COM_ID:
#     COM_NAME[COM_ID[x]] = x

# IDLENGTH = 1  # TODO Review and delete legacy data style
# DATALENGTH = 4

# # Good response -> Gxxxx
# # Bad response -> BBBBB
# Good_ID = b'G'
# Bad_ID = b'B'
#
# String_ID = b'"'

class SThread(QtCore.QThread):
    # sig_received = pyqtSignal(list)  # TODO Review this change with Andrei
    sig_received = pyqtSignal(object)  # TODO is it safe to generalize
    sig_print = pyqtSignal(str)

    def __init__(self, connection, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.connection = connection

        self.commandQueue = queue.Queue()

        self.errored = False

    # Function that adds a message of size 'word' to queue for sending. # TODO Review this data size
    def queueMessage(self, word):
        self.commandQueue.put_nowait(word)

    # Try to give (send) a message waiting in the queue back through the connection, eg Debug or SerialConnection
    def trySendMessage(self):
        try:
            word = self.commandQueue.get_nowait()
            self.commandQueue.task_done() #errored transmitions are not retried

            # Checks to see if one of pre-configed cmds. If it is, then it just sends the char associated with cmd
            bytes = None
            if word in COM_ID:
                bytes = COM_ID[word].encode('ascii')

            else:
                bytes = word.encode('ascii')

            self.connection.send(bytes)

            self.sig_print.emit("Sent!")

        except TimeoutException:
            self.sig_print.emit("Message timed-out!")

        except queue.Empty:
            pass

        except:
            self.sig_print.emit("Unexpected error while sending!")

    # Function that is run by the thread when it is not blocked
    def run(self):
        self.running = True  # TODO Review purpose of this
        # Loop that attempts a message send and gets+parses data repeatedly
        while self.running:
            time.sleep(0.01)  # TODO: REMOVE ME ( https://trello.com/c/KQ02vWL3 )
            self.trySendMessage()

            byteList = self.get_data()
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

    # Try to get (receive) data from the connection, such as Debug or SerialConnection
    def get_data(self):

        message = None

        try:
            message = self.connection.get()
            self.errored = False
        except XBeeException:  # TODO: use general exception in IConnection
            if not self.errored:
                self.errored = True
                self.sig_print.emit("Error reading data! Radio disconnected?")

        if not message:
            return []   # TODO Note this needs to be changed in data type refactoring

        data = message
        data = map(lambda x: bytes([x]), data)

        return list(data)  # TODO Note this needs to be changed in data type refactoring


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
