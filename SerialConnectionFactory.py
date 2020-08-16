from typing import Union

from IConnectionFactory import IConnectionFactory
from SerialConnection import SerialConnection


class SerialConnectionFactory(IConnectionFactory):

    def requiresComPort(self) -> bool:
        return True

    def requiresBaudRate(self) -> bool:
        return True

    def construct(self, comPort: Union[int, str, None] = None, baudRate: Union[int, None] = None):
        return SerialConnection(comPort, baudRate)
