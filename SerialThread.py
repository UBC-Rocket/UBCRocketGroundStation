import serial
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from digi.xbee.devices import XBeeDevice
from digi.xbee.devices import RemoteXBeeDevice
from digi.xbee.devices import XBee64BitAddress
from digi.xbee.exception import TimeoutException, XBeeException

IDLENGTH = 1
DATALENGTH = 4

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
    sig_received = pyqtSignal(list)
    sig_print = pyqtSignal(str)

    def __init__(self, com, ids, baud, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.device = XBeeDevice(com, baud)
        self.device.set_sync_ops_timeout(5) #5 seconds
        self.device.open()
        self.IdSet = ids
        self.IdSet.add(Good_ID)
        self.IdSet.add(Bad_ID)

    def send(self, word):

        bytes = None
        if word in COM_ID:
            bytes = COM_ID[word].encode('ascii')

        else:
            bytes = word.encode('ascii')

        try:
            #remote_device = RemoteXBeeDevice(self.device, XBee64BitAddress.from_hex_string("0013A20041678fb9"))
            #self.device.send_data(remote_device, bytes)
            self.device.send_data_broadcast(bytes)
        except TimeoutException:
            self.sig_print.emit("Message timed-out!")
        except:
            self.sig_print.emit("Unexpected error while sending!")

        self.sig_print.emit("Sent!")

    def run(self):
        self.running = True
        chunkLength = IDLENGTH + DATALENGTH
        byteList = []
        while self.running:
            byteList = self.get_api_data()
            #byteList.extend(newbytes)
            # print("Byte buffer: " + str(len(byteList)))

            while len(byteList) > 0:
                if byteList[0] == Good_ID: #Should be byteList[IDLENGTH:chunklength] ??
                    if try_ascii_decode(byteList[IDLENGTH]) and byteList[IDLENGTH].decode("ascii") in COM_NAME:
                        self.sig_print.emit("Successful " + COM_NAME[byteList[IDLENGTH].decode("ascii")])
                    else:
                        self.sig_print.emit("Successful 0x" + byteList[IDLENGTH].hex())
                    del byteList[0:2]

                elif byteList[0] == Bad_ID:
                    if try_ascii_decode(byteList[IDLENGTH]) and byteList[IDLENGTH].decode("ascii") in COM_NAME:
                        self.sig_print.emit("Failed " + COM_NAME[byteList[IDLENGTH].decode("ascii")])
                    else:
                        self.sig_print.emit("Failed 0x" + byteList[IDLENGTH].hex())
                    del byteList[0:2]

                elif byteList[0] == String_ID:
                    bytes = bytearray(map(_bytes_to_byte, byteList[1:len(byteList)]))
                    str = bytes.decode("ascii")
                    self.sig_print.emit(str)
                    del byteList[0:len(byteList)]

                elif len(byteList) >= chunkLength and byteList[0] in self.IdSet:
                    chunk = byteList[0:chunkLength]
                    data = list(map(_bytes_to_int, chunk))
                    self.sig_received.emit(data)
                    del byteList[0:chunkLength]

                elif len(byteList) > chunkLength:
                    del byteList[0]

                else:
                    break

    def get_api_data(self):

        message = None
        errored = False

        while message is None:
            try:
                message = self.device.read_data()
                errored = False
            except XBeeException:
                if not errored:
                    errored = True
                    self.sig_print.emit("Error reading data! Radio disconnected?")

        data = message.data
        data = map(lambda x: bytes([x]), data)


        return list(data)


def _bytes_to_int(bytes):
    return int.from_bytes(bytes, byteorder='little', signed=False)

def _bytes_to_byte(bytes):
    return bytes[0]


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
