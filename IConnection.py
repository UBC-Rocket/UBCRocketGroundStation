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

    # Called to upon shutdown. Clean-up tasks done here.
    @abc.abstractmethod
    def shutDown(self):
        pass

    # Returns whether ints should be decoded as big endian
    @abc.abstractmethod
    def isIntBigEndian(self):  # must be thead safe
        pass

    # Returns whether floats should be decoded as big endian
    @abc.abstractmethod
    def isFloatBigEndian(self):
        pass


class DataProviderException(Exception):
    pass
