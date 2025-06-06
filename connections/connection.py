from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Callable, Optional

ConnectionMessage = namedtuple('ConnectionMessage', ['device_address', 'connection', 'data'])


class Connection(ABC):
    @abstractmethod
    def registerCallback(self, fn: Callable[[ConnectionMessage], None]) -> None:
        """Register callback to which we will send new data.

        :param fn: Must be non-blocking and thread safe
        :type fn: typing.Callable[[bytearray], None]
        """
        pass

    # Send data to a specific device on this connection
    @abstractmethod
    def send(self, device_address: str, data) -> None:  # must be thead safe
        pass

    # Send data to all devices on this connection
    @abstractmethod
    def broadcast(self, data) -> None:  # must be thead safe
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

    # Returns the device address of the connection
    @abstractmethod
    def getDeviceAddress(self) -> Optional[str]:
        pass

    # Returns the KISS protocol connection address
    @abstractmethod
    def getKissAddress(self) -> Optional[str]:
        pass

    # Returns the stage number of the connection
    @abstractmethod
    def getStage(self) -> int:
        pass

    @abstractmethod
    def getNMEASerialPort(self) -> Optional[str]:
        pass

    @abstractmethod
    def getNMEABaudRate(self) -> Optional[int]:
        pass