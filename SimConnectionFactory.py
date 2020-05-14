from IConnectionFactory import IConnectionFactory
from SimConnection import SimConnection
from detail import *
import os

FIRMWARE_DIR = 'FW'
EXECUTABLE_NAME = 'program'
FILE_EXTENSION = {
    'win32':'.exe'
}


class SimConnectionFactory(IConnectionFactory):
    def construct(self, comPort=None, baudRate=None):
        executableName = EXECUTABLE_NAME

        if  sys.platform in FILE_EXTENSION.keys():
            executableName += FILE_EXTENSION[sys.platform]

        return SimConnection(os.path.join(LOCAL, FIRMWARE_DIR), executableName)

    def requiresComPort(self):
        return False

    def requiresBaudRate(self):
        return False
