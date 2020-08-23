from typing import Union

from ..connection_factory import ConnectionFactory
from .serial_connection import SerialConnection


class SerialConnectionFactory(ConnectionFactory):

    def requiresComPort(self) -> bool:
        return True

    def requiresBaudRate(self) -> bool:
        return True

    def construct(self, comPort: Union[int, str, None] = None, baudRate: Union[int, None] = None):
        return SerialConnection(comPort, baudRate)
