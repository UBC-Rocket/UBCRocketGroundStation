from ..rocket_profile import RocketProfile
from main_window.whistler_blackcomb.wb_app import WbApp
from main_window.whistler_blackcomb.wb_packet_parser import WbPacketParser
from main_window.competition.comp_packet_parser import CompPacketParser
from connections.debug.debug_connection import DebugConnection
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from main_window.device_manager import DeviceType


class WbProfile(RocketProfile):

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
    def mapping_device(self):
        return None

    @property
    def required_device_versions(self):
        return None

    def construct_serial_connection(self, com_port, baud_rate):
        return None

    def construct_debug_connection(self):
        return {
            'TANTALUS_STAGE_1_CONNECTION': DebugConnection('TANTALUS_STAGE_1_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE],
                                                           generate_radio_packets=False)
        }

    def construct_sim_connection(self):
        return None

    def construct_app(self, connections):
        return WbApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()  # TODO : Use WbPacketParser once its set up
        #return WbPacketParser()
