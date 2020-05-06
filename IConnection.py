import abc


class IConnection:
    @abc.abstractmethod
    def registerCallback(self, fn):  # fn(bytes) must be non-blocking and thread safe
        pass

    @abc.abstractmethod
    def send(self, data):  # must be thead safe
        pass


class DataProviderException(Exception):
    pass
