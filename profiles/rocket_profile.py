from abc import ABC, abstractmethod
from typing import Dict, List
from collections import namedtuple

from connections.connection import Connection
from main_window.packet_parser import PacketParser
from main_window.device_manager import DeviceType
from .label import Label

FlightPoint = namedtuple('FlightPoint', (
    'time',
    'time_tolerance',
    'altitude',
    'altitude_tolerance'
))

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
    def labels(self) -> List[Label]:
        pass

    @property
    @abstractmethod
    def expected_devices(self) -> List[DeviceType]:
        pass

    @property
    @abstractmethod
    def mapping_devices(self) -> List[DeviceType]:
        pass

    @property
    @abstractmethod
    def required_device_versions(self) -> Dict[DeviceType, str]:
        """
        :return: Optional restrictions on device versions
        """
        pass

    @property
    @abstractmethod
    def expected_apogee_point(self) -> FlightPoint:
        """
        :return: Point in flight where apogee/drogue is expected to occur
        """
        pass

    @property
    @abstractmethod
    def expected_main_deploy_point(self) -> FlightPoint:
        """
        :return: Point in flight where main parachute deployment is expected to occur
        """
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
