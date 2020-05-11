from DebugConnection import DebugConnection
from IConnectionFactory import IConnectionFactory


class DebugConnectionFactory(IConnectionFactory):
    def construct(self, comPort=None, baudRate=None):
        return DebugConnection()

    def requiresComPort(self):
        return False

    def requiresBaudRate(self):
        return False
