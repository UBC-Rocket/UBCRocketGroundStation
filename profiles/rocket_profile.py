from abc import ABC, abstractmethod
from typing import Iterable, Dict
from connections.connection import Connection
from main_window.packet_parser import PacketParser
from connections.sim.hw_sim import HWSim
from main_window.device_manager import DeviceType
from .label import Label


class RocketProfile(ABC):
    @property
    @abstractmethod
    def rocket_name(self) -> str:
        pass

    @property
    @abstractmethod
    def buttons(self) -> Dict[str, str]:
        pass

    @property
    @abstractmethod
    def labels(self) -> Iterable[Label]:
        pass

    @property
    @abstractmethod
    def mapping_device(self) -> DeviceType:
        pass

    '''
    Factory pattern for objects that should only be constructed if needed
    '''
    @abstractmethod
    def construct_serial_connection(self, com_port: str, baud_rate: int) -> Dict[str, Connection]:
        pass

    @abstractmethod
    def construct_debug_connection(self) -> Dict[str, Connection]:
        pass

    @abstractmethod
    def construct_sim_connection(self) -> Dict[str, Connection]:
        # Here we can define HW Sim and all its sensors etc. without them being constructed if we aren't running SIM.
        # This is useful as HW Sim may be multi-threaded or do something upon construction that we dont want to
        # happen during regular flight.
        pass

    @abstractmethod
    def construct_app(self, connections: Dict[str, Connection]):
        pass

    @abstractmethod
    def construct_packet_parser(self) -> PacketParser:
        pass
