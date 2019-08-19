from IConnectionFactory import IConnectionFactory
from SerialConnection import SerialConnection


class SerialConnectionFactory(IConnectionFactory):
    requiresBaudRate = True
    requiresComPort = True

    def construct(self, comPort=None, baudRate=None):
        return SerialConnection(comPort, baudRate)

