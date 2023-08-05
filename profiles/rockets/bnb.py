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
from connections.sim.hw.sensors.voltage_sensor_sim import VoltageSensor
from connections.sim.hw.ignitor_sim import Ignitor, IgnitorType
from connections.sim.hw.sensors.sensor_sim import SensorSim
from connections.sim.hw.rocket_sim import RocketSim, FlightDataType
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from util.detail import REQUIRED_FLARE


class BNBProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "BNB"

    @property
    def buttons(self):
        return {
            "Arm Stage 1": "BNB_STAGE_1_FLARE.ARM",
            "Ping Stage 1": "BNB_STAGE_1_FLARE.PING",
            "Arm Stage 2": "BNB_STAGE_2_FLARE.ARM",
            "Ping Stage 2": "BNB_STAGE_2_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.BNB_STAGE_1_FLARE, "Stage1Altitude", update_altitude, "Stage 1 Altitude"),
            Label(DeviceType.BNB_STAGE_1_FLARE, "Stage1MaxAltitude", update_max_altitude, "Stage 1 Max Altitude"),
            Label(DeviceType.BNB_STAGE_1_FLARE, "Stage1GPS", update_gps, "Stage 1 GPS"),
            Label(DeviceType.BNB_STAGE_1_FLARE, "Stage1State", update_state, "Stage 1 State"),
            Label(DeviceType.BNB_STAGE_1_FLARE, "Stage1Pressure", update_pressure, "Stage 1 Pressure"),
            Label(DeviceType.BNB_STAGE_1_FLARE, "Stage1Acceleration", update_acceleration, "Stage 1 Acceleration"),
            Label(DeviceType.BNB_STAGE_2_FLARE, "Stage2Altitude", update_altitude, "Stage 2 Altitude"),
            Label(DeviceType.BNB_STAGE_2_FLARE, "Stage2MaxAltitude", update_max_altitude, "Stage 2 Max Altitude"),
            Label(DeviceType.BNB_STAGE_2_FLARE, "Stage2GPS", update_gps, "Stage 2 GPS"),
            Label(DeviceType.BNB_STAGE_2_FLARE, "Stage2State", update_state, "Stage 2 State"),
            Label(DeviceType.BNB_STAGE_2_FLARE, "Stage2Pressure", update_pressure, "Stage 2 Pressure"),
            Label(DeviceType.BNB_STAGE_2_FLARE, "Stage2Acceleration", update_acceleration, "Stage 2 Acceleration"),
        ]

    @property
    def expected_devices(self):
        return [
            DeviceType.BNB_STAGE_1_FLARE,
            DeviceType.BNB_STAGE_2_FLARE,
        ]

    @property
    def mapping_devices(self):
        return [
            DeviceType.BNB_STAGE_1_FLARE,
            DeviceType.BNB_STAGE_2_FLARE,
        ]

    @property
    def required_device_versions(self):
        return {
            DeviceType.BNB_STAGE_1_FLARE: REQUIRED_FLARE,
            DeviceType.BNB_STAGE_2_FLARE: REQUIRED_FLARE,
        }

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
            'BNB_STAGE_1_CONNECTION': DebugConnection('BNB_STAGE_1_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_1_FLARE],
                                                           generate_radio_packets=True),

            'BNB_STAGE_2_CONNECTION': DebugConnection('BNB_STAGE_2_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_2_FLARE],
                                                           generate_radio_packets=True),
        }

    def construct_sim_connection(self):
        # Assemble HW here

        '''
        Stage 1
        '''
        rocket_sim_stage_1 = RocketSim('simple.ork') # TODO: Update ORK file once possible

        hw_sim_sensors_stage_1 = [
            DummySensor(SensorType.BAROMETER, (1000, 25)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            DummySensor(SensorType.ACCELEROMETER, (1, 0, 0)),
            DummySensor(SensorType.IMU, (1, 0, 0, 0, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
            VoltageSensor()
        ]

        hw_sim_ignitors_stage_1 = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35),
        ]

        hwsim_stage_1 = HWSim(rocket_sim_stage_1, hw_sim_sensors_stage_1, hw_sim_ignitors_stage_1)

        '''
        Stage 2
        '''
        rocket_sim_stage_2 = RocketSim('simple.ork') # TODO: Update ORK file once possible

        hw_sim_sensors_stage_2 = [
            DummySensor(SensorType.BAROMETER, (100000, 25)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            DummySensor(SensorType.ACCELEROMETER, (1, 0, 0)),
            DummySensor(SensorType.IMU, (1, 0, 0, 0, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
            VoltageSensor()
        ]

        hw_sim_ignitors_stage_2 = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35),
        ]

        hwsim_stage_2 = HWSim(rocket_sim_stage_2, hw_sim_sensors_stage_2, hw_sim_ignitors_stage_2)

        return {
            'BNB_STAGE_1_CONNECTION': SimConnection("BNBStage1", "0013A20041678FC0", hwsim_stage_1),
            'BNB_STAGE_2_CONNECTION': SimConnection("BNBStage2", "0013A20041678FC0", hwsim_stage_2),
        }

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()
