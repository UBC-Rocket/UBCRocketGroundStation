from ..label import (Label, update_acceleration, update_altitude,
                     update_chamber_pressure, update_chamber_temp, update_gps,
                     update_max_altitude, update_pressure, update_state,
                     update_tank_pressure)
from ..rocket_profile import RocketProfile
from connections.debug.debug_connection import DebugConnection
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from  main_window.device_manager import DeviceType


class CoPilotProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Co-Pilot"

    @property
    def buttons(self):
        return {
            "Arm": "CO_PILOT.ARM",
            "Halo": "CO_PILOT.halo",
            "Data": "CO_PILOT.data",
            "Ping": "CO_PILOT.PING"
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.CO_PILOT, "Altitude", update_altitude),
            Label(DeviceType.CO_PILOT, "MaxAltitude", update_max_altitude, "Max Altitude"),
            Label(DeviceType.CO_PILOT, "GPS", update_gps),
            Label(DeviceType.CO_PILOT, "State", update_state),
            Label(DeviceType.CO_PILOT, "Pressure", update_pressure),
            Label(DeviceType.CO_PILOT, "Acceleration", update_acceleration),
            Label(DeviceType.CO_PILOT, "TankPressure", update_tank_pressure, "Tank Pressure"),
            Label(DeviceType.CO_PILOT, "ChamberPressure", update_chamber_pressure, "Chamber Pressure"),
            Label(DeviceType.CO_PILOT, "ChamberTemp", update_chamber_temp, "Chamber Temperature"),
        ]

    @property
    def mapping_device(self):
        return DeviceType.CO_PILOT

    def construct_serial_connection(self, com_port, baud_rate):
        return None

    def construct_debug_connection(self):
        return [
            DebugConnection('CoPilot_HWID', 0x02, generate_radio_packets=True),
        ]

    def construct_sim_connection(self):
        return None

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()
