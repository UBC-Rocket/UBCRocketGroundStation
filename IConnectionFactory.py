import abc


class IConnectionFactory:
    requiresComPort = False
    requiresBaudRate = False

    @abc.abstractmethod
    def construct(self, comPort=None, baudRate=None):
        pass
