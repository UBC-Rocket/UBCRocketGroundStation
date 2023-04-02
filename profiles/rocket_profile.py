from abc import ABC, abstractmethod
from typing import Dict, List
from collections import namedtuple

from connections.connection import Connection
from main_window.data_entry_id import DataEntryIds
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
    def all_labels(self) -> List[Label]:
        """
        :return: All labels with data, not just those displayed in main window
        """
        return self.labels

    @property
    @abstractmethod
    def expected_devices(self) -> List[DeviceType]:
        """
        :return: Devices of rocket
        """
        pass

    @property
    @abstractmethod
    def mapping_devices(self) -> List[DeviceType]:
        """
        :return: Devices to put on map
        """
        pass

    @property
    @abstractmethod
    def required_device_versions(self) -> Dict[DeviceType, str]:
        """
        :return: Optional restrictions on device versions
        """
        pass

    @property
    def label_to_data_id(self):
        """
        Convert label name to DataEntryId
        """
        return {"Altitude": DataEntryIds.CALCULATED_ALTITUDE,
                "MaxAltitude": None,
                "State": DataEntryIds.STATE,
                "Pressure": DataEntryIds.PRESSURE,
                "Acceleration": [DataEntryIds.ACCELERATION_X, DataEntryIds.ACCELERATION_Y,
                                 DataEntryIds.ACCELERATION_Z]
                }

    @property
    def label_unit(self):
        """
        Units for labels
        """
        return {"Altitude": "m",
                "MaxAltitude": "m",
                "State": "",
                "Pressure": "",
                "Acceleration": "g",
                }

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

    """
    Factory pattern for objects that should only be constructed if needed
    """

    @abstractmethod
    def construct_serial_connection(
            self, com_port: str, baud_rate: int
    ) -> Dict[str, Connection]:
        pass

    @abstractmethod
    def construct_debug_connection(self) -> Dict[str, Connection]:
        pass

    @abstractmethod
    def construct_sim_connection(self) -> Dict[str, Connection]:
        # Here we can define HW Sim and all its sensors etc.
        # without them being constructed if we aren't running SIM.
        # This is useful as HW Sim may be multi-threaded or do something
        # upon construction that we dont want to happen during regular flight.
        pass

    @abstractmethod
    def construct_app(self, connections: Dict[str, Connection]):
        pass

    @abstractmethod
    def construct_packet_parser(self) -> PacketParser:
        pass
