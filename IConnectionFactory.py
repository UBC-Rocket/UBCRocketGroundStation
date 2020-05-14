import abc


class IConnectionFactory:
    @abc.abstractmethod
    def requiresComPort(self):
        return False

    @abc.abstractmethod
    def requiresBaudRate(self):
        return False

    @abc.abstractmethod
    def construct(self, comPort=None, baudRate=None):
        pass
