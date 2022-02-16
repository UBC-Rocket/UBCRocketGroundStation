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
from connections.sim.hw.clock_sim import Clock
from connections.sim.hw.hw_sim import HWSim
from connections.sim.hw.sensors.sensor import SensorType
from connections.sim.hw.sensors.dummy_sensor import DummySensor
from connections.sim.hw.ignitor_sim import Ignitor, IgnitorType
from connections.sim.hw.sensors.voltage_sensor_sim import VoltageSensor
from connections.sim.hw.sensors.sensor_sim import SensorSim
from connections.sim.hw.rocket_sim import RocketSim, FlightDataType
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from util.detail import REQUIRED_FLARE


class HollyburnProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Hollyburn"

    @property
    def buttons(self):
        return {
            "Arm Body": "HOLLYBURN_BODY_FLARE.ARM",
            "Ping Body": "HOLLYBURN_BODY_FLARE.PING",
            "Arm Nose": "HOLLYBURN_NOSE_FLARE.ARM",
            "Ping Nose": "HOLLYBURN_NOSE_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.HOLLYBURN_BODY_FLARE, "Altitude", update_altitude),
            Label(DeviceType.HOLLYBURN_BODY_FLARE, "MaxAltitude", update_max_altitude, "Max Altitude"),
            Label(DeviceType.HOLLYBURN_BODY_FLARE, "GPS", update_gps),
            Label(DeviceType.HOLLYBURN_BODY_FLARE, "State", update_state),
            Label(DeviceType.HOLLYBURN_BODY_FLARE, "Pressure", update_pressure),
            Label(DeviceType.HOLLYBURN_BODY_FLARE, "Acceleration", update_acceleration),
            Label(DeviceType.HOLLYBURN_NOSE_FLARE, "Stage2State", update_state, "Nose State"),
            Label(DeviceType.HOLLYBURN_NOSE_FLARE, "Stage2Gps", update_gps, "Nose GPS"),
        ]

    @property
    def expected_devices(self):
        return [
            DeviceType.HOLLYBURN_BODY_FLARE,
            # DeviceType.HOLLYBURN_NOSE_FLARE,
        ]

    @property
    def mapping_devices(self):
        return [DeviceType.HOLLYBURN_NOSE_FLARE]

    @property
    def required_device_versions(self):
        return {
            DeviceType.HOLLYBURN_BODY_FLARE: REQUIRED_FLARE,
            DeviceType.HOLLYBURN_NOSE_FLARE: REQUIRED_FLARE,
        }

    @property
    def expected_apogee_point(self):
        return FlightPoint(
            time=15.96,
            time_tolerance=5,
            altitude=944,
            altitude_tolerance=30
        )

    @property
    def expected_main_deploy_point(self):
        return FlightPoint(
            time=89.29,
            time_tolerance=5,
            altitude=488,
            altitude_tolerance=50
        )

    def construct_serial_connection(self, com_port, baud_rate):
        return {
            'XBEE_RADIO': SerialConnection(com_port, baud_rate),
        }

    def construct_debug_connection(self):
        return {
            'HOLLYBURN_BODY_FLARE_CONNECTION': DebugConnection('HOLLYBURN_BODY_FLARE_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.HOLLYBURN_BODY_FLARE],
                                                           generate_radio_packets=True),

            'HOLLYBURN_NOSE_FLARE_CONNECTION': DebugConnection('HOLLYBURN_NOSE_FLARE_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.HOLLYBURN_NOSE_FLARE],
                                                           generate_radio_packets=True),
        }

    def construct_sim_connection(self):
        # Assemble HW here

        '''
        Body
        '''
        rocket_sim_body = RocketSim('Hollyburn CanSat Jan 20.ork')

        hw_sim_sensors_body = [
            SensorSim(SensorType.BAROMETER, rocket_sim_body, error_stdev=(50, 0.005)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            SensorSim(SensorType.ACCELEROMETER, rocket_sim_body),
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
            VoltageSensor()
        ]

        hw_sim_ignitors_body = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16, action_fn=rocket_sim_body.deploy_main),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35, action_fn=rocket_sim_body.deploy_drogue),
        ]

        hwsim_body = HWSim(rocket_sim_body, hw_sim_sensors_body, hw_sim_ignitors_body)

        '''
        Nose
        '''

        # TODO: Enable this once possible
        '''
        rocket_sim_nose = RocketSim('Hollyburn CanSat Jan 20.ork')

        hw_sim_sensors_nose = [
            SensorSim(SensorType.BAROMETER, rocket_sim_nose, error_stdev=(50, 0.005)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            SensorSim(SensorType.ACCELEROMETER, rocket_sim_nose),
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
        ]

        hw_sim_ignitors_nose = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16, action_fn=rocket_sim_body.deploy_main),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35, action_fn=rocket_sim_body.deploy_drogue),
        ]

        hwsim_nose = HWSim(rocket_sim_nose, hw_sim_sensors_nose, hw_sim_ignitors_nose)
        '''

        return {
            'HOLLYBURN_BODY_CONNECTION': SimConnection("Hollyburn", "0013A20041678FC0", hwsim_body),
            # 'HOLLYBURN_NOSE_CONNECTION': SimConnection("Hollyburn", "0013A20041678FC0", hwsim_nose),
        }

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()
