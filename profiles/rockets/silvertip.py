from connections.sim.hw.sensors.sensor_sim import SensorSim
from ..label import (
    Label,
    update_acceleration,
    update_altitude,
    update_gps,
    update_max_altitude,
    update_pressure,
    update_state,
)
from ..rocket_profile import RocketProfile, FlightPoint
from connections.serial.serial_connection import SerialConnection
from connections.debug.debug_connection import DebugConnection
from connections.sim.sim_connection import SimConnection
from connections.sim.hw.hw_sim import HWSim
from connections.sim.hw.sensors.sensor import SensorType
from connections.sim.hw.sensors.dummy_sensor import DummySensor
from connections.sim.hw.sensors.voltage_sensor_sim import VoltageSensor
from connections.sim.hw.ignitor_sim import Ignitor, IgnitorType
from connections.sim.hw.rocket_sim import RocketSim, FlightDataType
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from util.detail import REQUIRED_FLARE


class SilvertipProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Silvertip"

    @property
    def buttons(self):
        return {
            "Arm": "SILVERTIP_FLARE.ARM",
            "Ping": "SILVERTIP_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.SILVERTIP_FLARE, "Altitude", update_altitude),
            Label(DeviceType.SILVERTIP_FLARE, "MaxAltitude", update_max_altitude, "Max Altitude"),
            Label(DeviceType.SILVERTIP_FLARE, "GPS", update_gps),
            Label(DeviceType.SILVERTIP_FLARE, "State", update_state),
            Label(DeviceType.SILVERTIP_FLARE, "Pressure", update_pressure),
            Label(DeviceType.SILVERTIP_FLARE, "Acceleration", update_acceleration),
        ]

    @property
    def expected_devices(self):
        return [DeviceType.SILVERTIP_FLARE]

    @property
    def mapping_devices(self):
        return [DeviceType.SILVERTIP_FLARE]

    @property
    def required_device_versions(self):
        return {
            DeviceType.SILVERTIP_FLARE: REQUIRED_FLARE
        }

    @property
    def expected_apogee_point(self):
        return FlightPoint(
            time=35.9,
            time_tolerance=5,
            altitude=7603,
            altitude_tolerance=30
        )

    @property
    def expected_main_deploy_point(self):
        return FlightPoint(
            time=514.4,
            time_tolerance=5,
            altitude=590,
            altitude_tolerance=50
        )

    def construct_serial_connection(self, com_port, baud_rate):
        return {
            'XBEE_RADIO': SerialConnection(com_port, baud_rate),
        }

    def construct_debug_connection(self):
        return {
            'SILVERTIP_FLARE_CONNECTION': DebugConnection('SILVERTIP_FLARE_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.SILVERTIP_FLARE],
                                                           generate_radio_packets=True),
        }

    def construct_sim_connection(self):
        # Assemble HW here

        rocket_sim = RocketSim('Silvertip-01-05-2022.ork')

        hw_sim_sensors = [ # TODO: Use different values than Tantalus
            SensorSim(SensorType.BAROMETER, rocket_sim, error_stdev=(50, 0.005)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            SensorSim(SensorType.ACCELEROMETER, rocket_sim),
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
            VoltageSensor()
        ]

        hw_sim_ignitors = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16, action_fn=rocket_sim.deploy_main),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35, action_fn=rocket_sim.deploy_drogue),
        ]

        hwsim = HWSim(rocket_sim, hw_sim_sensors, hw_sim_ignitors)

        return {
            'SILVERTIP_CONNECTION': SimConnection("Silvertip", "0013A20041678FC0", hwsim),
        }

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()