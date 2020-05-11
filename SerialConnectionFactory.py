from IConnectionFactory import IConnectionFactory
from SerialConnection import SerialConnection


class SerialConnectionFactory(IConnectionFactory):

    def requiresComPort(self):
        return True

    def requiresBaudRate(self):
        return True

    def construct(self, comPort=None, baudRate=None):
        return SerialConnection(comPort, baudRate)

