import abc
from typing import Callable


class Connection(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def registerCallback(self, fn: Callable[[bytearray], None]) -> None:
        """Register callback to which we will send new data.

        :param fn: Must be non-blocking and thread safe
        :type fn: typing.Callable[[bytearray], None]
        """
        pass

    # Send data to connection
    @abc.abstractmethod
    def send(self, data) -> None:  # must be thead safe
        pass

    # Called to upon shutdown. Clean-up tasks done here.
    @abc.abstractmethod
    def shutDown(self) -> None:
        pass

    # Returns whether ints should be decoded as big endian
    @abc.abstractmethod
    def isIntBigEndian(self) -> None:  # must be thead safe
        pass

    # Returns whether floats should be decoded as big endian
    @abc.abstractmethod
    def isFloatBigEndian(self) -> None:
        pass


class DataProviderException(Exception):
    pass
