import abc


class IConnection:
    @abc.abstractmethod
    def get(self):  # Non blocking
        pass

    @abc.abstractmethod
    def send(self, data):
        pass


class DataProviderException(Exception):
    pass
