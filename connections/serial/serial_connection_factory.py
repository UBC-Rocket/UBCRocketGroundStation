from typing import Union

from ..connection_factory import ConnectionFactory
from .serial_connection import SerialConnection


class SerialConnectionFactory(ConnectionFactory):

    @property
    def connection_name(self) -> str:
        return "Serial"

    @property
    def requires_com_port(self) -> bool:
        return True

    @property
    def requires_baud_rate(self) -> bool:
        return True

    def construct(
        self,
        comPort: Union[int, str, None] = None,
        baudRate: Union[int, None] = None,
        rocket=None,
    ):
        return SerialConnection(comPort, baudRate)
