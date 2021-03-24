from connections.sim.hw.hw_sim import HWSim
from connections.sim.hw.ignitor_sim import Ignitor, IgnitorType
from connections.sim.hw.rocket_sim import RocketSim
from connections.sim.hw.sensors.dummy_sensor import DummySensor
from connections.sim.hw.sensors.sensor import SensorType
from connections.sim.hw.sensors.sensor_sim import SensorSim
from connections.sim.sim_connection import SimConnection
from ..rocket_profile import RocketProfile, FlightPoint
from main_window.whistler_blackcomb.wb_app import WbApp
from main_window.competition.comp_app import CompApp
from main_window.whistler_blackcomb.wb_packet_parser import WbPacketParser
from main_window.competition.comp_packet_parser import CompPacketParser
from connections.debug.debug_connection import DebugConnection
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from main_window.device_manager import DeviceType

from util.detail import REQUIRED_WB_FIRMWARE

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
            "Ping": "WB_FIRMWARE.PING",
            "Abort": "WB_FIRMWARE.ABORT",
            "Next Ground State": "WB_FIRMWARE.NEXT_STATE",
            "Actuate MOV": "WB_FIRMWARE.MOV",
            "Actuate MFV": "WB_FIRMWARE.MFV",
            "Actuate LOX Bleed": "WB_FIRMWARE.LOX_BLEED",
            "Actuate LOX Vent": "WB_FIRMWARE.LOX_VENT",
            "Actuate Fuel Bleed": "WB_FIRMWARE.FUEL_BLEED",
            "Actuate Fuel Vent": "WB_FIRMWARE.FUEL_VENT",
            "Actuate LOX Press": "WB_FIRMWARE.LOX_PRESS",
            "Actuate Fuel Press": "WB_FIRMWARE.FUEL_PRESS",
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
        return {DeviceType.WB_FIRMWARE: REQUIRED_WB_FIRMWARE}

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
            'WB_CONNECTION': DebugConnection('WHISTLER_BLACKCOMB_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.WB_FIRMWARE],
                                                           generate_radio_packets=True)
        }

    def construct_sim_connection(self):

        # TODO: Change this to actual wb profile when it's actually made on open rocket
        rocket_sim = RocketSim('Hollyburn CanSat Jan 20.ork')

        hw_sim_sensors = [
            SensorSim(SensorType.BAROMETER, rocket_sim, error_stdev=(50, 0.005)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            SensorSim(SensorType.ACCELEROMETER, rocket_sim),
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
        ]

        hw_sim_ignitors = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16, action_fn=rocket_sim.deploy_main),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35, action_fn=rocket_sim.deploy_drogue),
        ]

        hwsim = HWSim(rocket_sim, hw_sim_sensors, hw_sim_ignitors)

        return {
            'WB_CONNECTION': SimConnection("whistler-blackcomb", "0013A20041678FC0", hwsim),
        }

    def construct_app(self, connections):
        # return WbApp(connections, self)
        return CompApp(connections, self)

    def construct_packet_parser(self):
        # return CompPacketParser()  # TODO : Use WbPacketParser once its set up
        return WbPacketParser()
