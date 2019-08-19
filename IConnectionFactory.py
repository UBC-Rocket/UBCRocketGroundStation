import abc


class ConnectionFactory:
    requiresComPort = None
    requiresBaudRate = None

    @abc.abstractmethod
    def construct(self, comPort=None, baudRate=None):
        pass
