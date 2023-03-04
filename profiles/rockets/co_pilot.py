"""Profile for Co Pilot"""

from connections.debug.debug_connection import DebugConnection
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from util.detail import REQUIRED_FLARE
from ..label import (
    Label,
    update_acceleration,
    update_altitude,
    update_chamber_pressure,
    update_chamber_temp,
    update_gps,
    update_max_altitude,
    update_pressure,
    update_state,
    update_tank_pressure,
)
from ..rocket_profile import RocketProfile


class CoPilotProfile(RocketProfile):
    """Co Pilot"""
    @property
    def rocket_name(self):
        return "Co-Pilot"

    @property
    def buttons(self):
        return {
            "Arm": "CO_PILOT_FLARE.ARM",
            "Halo": "CO_PILOT_FLARE.halo",
            "Data": "CO_PILOT_FLARE.data",
            "Ping": "CO_PILOT_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.CO_PILOT_FLARE, "Altitude", update_altitude),
            Label(
                DeviceType.CO_PILOT_FLARE,
                "MaxAltitude",
                update_max_altitude,
                "Max Altitude",
            ),
            Label(DeviceType.CO_PILOT_FLARE, "GPS", update_gps),
            Label(DeviceType.CO_PILOT_FLARE, "State", update_state),
            Label(DeviceType.CO_PILOT_FLARE, "Pressure", update_pressure),
            Label(DeviceType.CO_PILOT_FLARE, "Acceleration", update_acceleration),
            Label(
                DeviceType.CO_PILOT_FLARE,
                "TankPressure",
                update_tank_pressure,
                "Tank Pressure",
            ),
            Label(
                DeviceType.CO_PILOT_FLARE,
                "ChamberPressure",
                update_chamber_pressure,
                "Chamber Pressure",
            ),
            Label(
                DeviceType.CO_PILOT_FLARE,
                "ChamberTemp",
                update_chamber_temp,
                "Chamber Temperature",
            ),
        ]

    @property
    def expected_devices(self):
        return [DeviceType.CO_PILOT_FLARE]

    @property
    def mapping_devices(self):
        return [DeviceType.CO_PILOT_FLARE]

    @property
    def required_device_versions(self):
        return {DeviceType.CO_PILOT_FLARE: REQUIRED_FLARE}

    @property
    def expected_apogee_point(self):
        return None

    @property
    def expected_main_deploy_point(self):
        return None

    def construct_serial_connection(self, com_port, baud_rate):
        return None

    def construct_debug_connection(self):
        return {
            "CO_PILOT_CONNECTION": DebugConnection(
                "CO_PILOT_RADIO_ADDRESS",
                DEVICE_TYPE_TO_ID[DeviceType.CO_PILOT_FLARE],
                generate_radio_packets=True,
            ),
        }

    def construct_sim_connection(self):
        return None

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()
