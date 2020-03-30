from typing import Dict

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from digi.xbee.exception import TimeoutException, XBeeException
import queue

import RadioController
import RocketData

IDLENGTH = 1  # TODO change these with new Radio protocol
DATALENGTH = 4  # TODO change these with new Radio protocol

COM_ID = {
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

# Good response -> Gxxxx
# Bad response -> BBBBB
Good_ID = b'G'
Bad_ID = b'B'

String_ID = b'"'

COM_NAME = {}
for x in COM_ID:
    COM_NAME[COM_ID[x]] = x

class SThread(QtCore.QThread):
    # sig_received = pyqtSignal(list)  # TODO Review this change with Andrei
    sig_received = pyqtSignal(object)  # TODO is it safe to generalize
    sig_print = pyqtSignal(str)

    def __init__(self, connection, ids, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.IdSet = ids
        self.IdSet.add(Good_ID)
        self.IdSet.add(Bad_ID)

        self.commandQueue = queue.Queue()

        self.errored = False

    def queueMessage(self, word):
        self.commandQueue.put_nowait(word)

    def trySendMessage(self):
        try:
            word = self.commandQueue.get_nowait()
            self.commandQueue.task_done() #errored transmitions are not retried

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

    def run(self):
        self.running = True
        chunk_length = IDLENGTH + DATALENGTH
        byteList = []
        while self.running:
            self.trySendMessage()

            byteList = self.get_data()
            while len(byteList) > 0:
                # if byteList[0] == Good_ID: #Should be byteList[IDLENGTH:chunklength] ??
                #     if try_ascii_decode(byteList[IDLENGTH]) and byteList[IDLENGTH].decode("ascii") in COM_NAME:
                #         self.sig_print.emit("Successful " + COM_NAME[byteList[IDLENGTH].decode("ascii")])
                #     else:
                #         self.sig_print.emit("Successful 0x" + byteList[IDLENGTH].hex())
                #     del byteList[0:2]
                #
                # elif byteList[0] == Bad_ID:
                #     if try_ascii_decode(byteList[IDLENGTH]) and byteList[IDLENGTH].decode("ascii") in COM_NAME:
                #         self.sig_print.emit("Failed " + COM_NAME[byteList[IDLENGTH].decode("ascii")])
                #     else:
                #         self.sig_print.emit("Failed 0x" + byteList[IDLENGTH].hex())
                #     del byteList[0:2]
                #
                # elif byteList[0] == String_ID:
                #     bytes = bytearray(map(_bytes_to_byte, byteList[1:len(byteList)]))
                #     str = bytes.decode("ascii")
                #     self.sig_print.emit(str)
                #     del byteList[0:len(byteList)]

                # calculate length (if possible)
                try:
                    data_and_info: Dict[str, int] = RadioController.extract_subpacket(byteList)
                except ValueError:
                    del byteList[0:1]
                    continue
                except Exception as e:
                    print(e)
                    del byteList[0:1]
                    continue

                chunk_length = data_and_info['length']
                data = byteList[0:chunk_length]  # convert all of the data in the chunk to byte

                parsed_subpacket_data = RadioController.parse_data( data_and_info['id'], data, chunk_length )

                # TODO call corresponding rocket data function to save?
                self.sig_received.emit(parsed_subpacket_data)  # transmit it

                del byteList[0:chunk_length]


                # if len(byteList) >= chunk_length and int.from_bytes(byteList[0], "big") in RadioController.PACKET_ID_TO_TYPE:  # TOD change to just working on any packet aka SECOND CONDITION ONLY?
                #     data_and_info = RadioController.extract_subpacket(byteList)
                #     data = bytearray(
                #         map(_bytes_to_byte, data_and_info.data_unit)
                #     )  # convert all of the data in the chunk to byte
                #
                #     RadioController.parse_data(
                #         data_and_info.type_id, data, data_and_info.length
                #     )  # TOD Pass along the parsed_data_Unit type and name info for
                #     self.sig_received.emit(data)  # transmit it
                #     del byteList[0:chunk_length]

                # elif len(byteList) > chunkLength:
                #     del byteList[0]
                #
                # else:
                #     break

    def get_data(self):

        message = None

        try:
            message = self.connection.get()
            self.errored = False
        except XBeeException: #TODO: use general exception in IConnection
            if not self.errored:
                self.errored = True
                self.sig_print.emit("Error reading data! Radio disconnected?")

        if not message:
            return []

        data = message
        data = map(lambda x: bytes([x]), data)

        return list(data)


def _bytes_to_int(bytes):
    return int.from_bytes(bytes, byteorder='little', signed=False)  # TODO review this byteorder

def _bytes_to_byte(bytes):
    return bytes[0]

def _byte_list_to_bytearray(byte_list):
    ba = bytearray()
    for byte in byte_list:
        ba.append(int.from_bytes(byte, byteorder="big", signed='false')) # TODO review this byteorder
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
