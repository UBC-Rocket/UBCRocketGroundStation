from typing import Union

from DebugConnection import DebugConnection
from IConnectionFactory import IConnectionFactory


class DebugConnectionFactory(IConnectionFactory):

    def requiresComPort(self) -> bool:
        return False

    def requiresBaudRate(self) -> bool:
        return False

    def construct(self, comPort: Union[int, str, None] = None, baudRate=None) -> DebugConnection:
        return DebugConnection()
