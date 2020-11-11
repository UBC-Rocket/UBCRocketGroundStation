from typing import Union

from ..connection_factory import ConnectionFactory
from .debug_connection import DebugConnection


class DebugConnectionFactory(ConnectionFactory):

    @property
    def connection_name(self) -> str:
        return "Debug"

    @property
    def requires_com_port(self) -> bool:
        return False

    @property
    def requires_baud_rate(self) -> bool:
        return False

    def construct(
        self, comPort: Union[int, str, None] = None, baudRate=None, rocket=None
    ) -> DebugConnection:
        return DebugConnection(generate_radio_packets=True)
