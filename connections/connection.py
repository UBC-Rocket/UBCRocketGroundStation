from abc import ABC, abstractmethod
from typing import Callable


class Connection(ABC):
    @abstractmethod
    def registerCallback(self, fn: Callable[[bytearray], None]) -> None:
        """Register callback to which we will send new data.

        :param fn: Must be non-blocking and thread safe
        :type fn: typing.Callable[[bytearray], None]
        """
        pass

    # Send data to connection
    @abstractmethod
    def send(self, data) -> None:  # must be thead safe
        pass

    # Called to upon shutdown. Clean-up tasks done here.
    @abstractmethod
    def shutdown(self) -> None:
        pass

    # Returns whether ints should be decoded as big endian
    @abstractmethod
    def isIntBigEndian(self) -> bool:  # must be thead safe
        pass

    # Returns whether floats should be decoded as big endian
    @abstractmethod
    def isFloatBigEndian(self) -> bool:
        pass


class DataProviderException(Exception):
    pass
