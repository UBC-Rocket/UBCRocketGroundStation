from typing import Union

from ..connection_factory import ConnectionFactory
from .debug_connection import DebugConnection


class DebugConnectionFactory(ConnectionFactory):

    def requiresComPort(self) -> bool:
        return False

    def requiresBaudRate(self) -> bool:
        return False

    def construct(self, comPort: Union[int, str, None] = None, baudRate=None) -> DebugConnection:
        return DebugConnection()
