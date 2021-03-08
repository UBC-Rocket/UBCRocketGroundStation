from ..rocket_profile import RocketProfile, FlightPoint
from main_window.whistler_blackcomb.wb_app import WbApp
from main_window.competition.comp_app import CompApp
from main_window.whistler_blackcomb.wb_packet_parser import WbPacketParser
from main_window.competition.comp_packet_parser import CompPacketParser
from connections.debug.debug_connection import DebugConnection
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from main_window.device_manager import DeviceType

from util.detail import REQUIRED_FLARE

from ..label import (
    Label,
    update_altitude,
)

class WbProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Whistler Blackcomb"

    @property
    def buttons(self):
        return {
            "Ping": "TANTALUS_STAGE_1_FLARE.ARM",
            "Abort": "WB_FIRMWARE.PING",
            "Next Ground State": "TANTALUS_STAGE_2_FLARE.ARM",
            "Actuate MOV": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate MFV": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate LOX Bleed": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate LOX Vent": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate Fuel Bleed": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate Fuel Vent": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate LOX Press": "TANTALUS_STAGE_2_FLARE.PING",
            "Actuate Fuel Press": "TANTALUS_STAGE_2_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.WB_FIRMWARE, "Altitude", update_altitude),
        ]

    @property
    def expected_devices(self):
        return [DeviceType.WB_FIRMWARE]

    @property
    def mapping_device(self):
        return DeviceType.WB_FIRMWARE

    @property
    def required_device_versions(self):
        return {DeviceType.WB_FIRMWARE: REQUIRED_FLARE}

    @property
    def expected_apogee_point(self):
        return None

    @property
    def expected_main_deploy_point(self):
        return None

    def construct_serial_connection(self, com_port, baud_rate):
        return {
            'XBEE_RADIO': SerialConnection(com_port, baud_rate),
        }

    def construct_debug_connection(self):
        return {
            'WB_CONNECTION': DebugConnection('TANTALUS_STAGE_1_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.WB_FIRMWARE],
                                                           generate_radio_packets=False)
        }

    def construct_sim_connection(self):
        return None

    def construct_app(self, connections):
        # return WbApp(connections, self)
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()  # TODO : Use WbPacketParser once its set up
        #return WbPacketParser()
