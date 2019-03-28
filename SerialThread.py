import serial
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

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
    "drogue": 'd'
}

# Good response -> Gxxxx
# Bad response -> BBBBB
Good_ID = 'G'.encode('ascii')
Bad_ID = 'B'.encode('ascii')

COM_NAME = {}
for x in COM_ID:
    COM_NAME[COM_ID[x]] = x

class SThread(QtCore.QThread):
    sig_received = pyqtSignal(list)
    sig_print = pyqtSignal(str)

    def __init__(self, com, ids, baud, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.ser = serial.Serial("COM" + str(com), baud)
        self.IdSet = ids
        self.IdSet.add(Good_ID)
        self.IdSet.add(Bad_ID)

    def send(self, word):

        if word in COM_ID:
            bytes = COM_ID[word].encode('ascii') * (IDLENGTH + DATALENGTH)
            self.ser.write(bytes)

        else:
            bytes = word.encode('ascii')
            self.ser.write(bytes)

        self.sig_print.emit("Sent!")

    def run(self):
        self.running = True
        chunkLength = IDLENGTH + DATALENGTH
        byteList = []
        while self.running:
            newbyte = self.ser.read(1)
            byteList.append(newbyte)
            # print("Byte buffer: " + str(len(byteList)))

            while len(byteList) >= chunkLength:
                if byteList[0] == Good_ID and byteList[IDLENGTH].decode("ascii") in COM_NAME.keys() and _are_all(
                        byteList[IDLENGTH:DATALENGTH], byteList[IDLENGTH]):
                    self.sig_print.emit("Successful " + COM_NAME[byteList[IDLENGTH].decode("ascii")])
                    del byteList[0:chunkLength]

                elif _are_all(byteList[0:chunkLength], Bad_ID):
                    self.sig_print.emit("Failure!")
                    del byteList[0:chunkLength]

                elif len(byteList) > chunkLength and byteList[0] in self.IdSet and byteList[chunkLength] in self.IdSet:
                    chunk = byteList[0:chunkLength]
                    data = list(map(_bytes_to_int, chunk))
                    self.sig_received.emit(data)
                    del byteList[0:chunkLength]

                elif len(byteList) > chunkLength:
                    del byteList[0]

                else:
                    break

def _bytes_to_int(bytes):
    return int.from_bytes(bytes, byteorder='little', signed=False)

def _bytes_to_byte(bytes):
    return bytes[0]


def _are_all(list, expected):
    for x in list:
        if x != expected:
            return False
    return True