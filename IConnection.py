import abc


class IConnection:

    # Register callback to which we will send new data
    @abc.abstractmethod
    def registerCallback(self, fn):  # fn(bytes) must be non-blocking and thread safe
        pass

    # Send data to connection
    @abc.abstractmethod
    def send(self, data):  # must be thead safe
        pass


class DataProviderException(Exception):
    pass
