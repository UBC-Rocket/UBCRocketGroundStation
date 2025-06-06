"""Profile for Whistler Blackcomb"""

from typing import Optional

from connections.debug.debug_connection import DebugConnection
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from main_window.whistler_blackcomb.wb_app import WbApp
from ..rocket_profile import RocketProfile


class WbProfile(RocketProfile):
    """Whistler Blackcomb"""
    @property
    def rocket_name(self):
        return "Whistler Blackcomb"

    @property
    def buttons(self):
        return None

    @property
    def labels(self):
        return None

    @property
    def expected_devices(self):
        return None

    @property
    def mapping_devices(self):
        return None

    @property
    def required_device_versions(self):
        return None

    @property
    def expected_apogee_point(self):
        return None

    @property
    def expected_main_deploy_point(self):
        return None

    def construct_serial_connection(self, com_port: str, baud_rate: int, nmea_serial_port: Optional[str], nmea_baud_rate: Optional[int]):
        return None

    def construct_debug_connection(self, nmea_serial_port: Optional[str], nmea_baud_rate: Optional[int]):
        return {
            'TANTALUS_STAGE_1_CONNECTION': DebugConnection('TANTALUS_STAGE_1_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE],
                                                           generate_radio_packets=False,
                                                           nmea_serial_port=nmea_serial_port,
                                                           nmea_baud_rate=nmea_baud_rate)
        }

    def construct_sim_connection(self, nmea_serial_port: Optional[str], nmea_baud_rate: Optional[int]):
        return None

    def construct_app(self, connections):
        return WbApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()  # TODO : Use WbPacketParser once its set up
        # return WbPacketParser()
