from ..label import (
    Label,
    update_acceleration,
    update_altitude,
    update_gps,
    update_max_altitude,
    update_pressure,
    update_state,
    update_aprs,
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


class TantalusProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Tantalus"

    @property
    def buttons(self):
        return {
            "Arm Stage 1": "TANTALUS_STAGE_1_FLARE.ARM",
            "Ping Stage 1": "TANTALUS_STAGE_1_FLARE.PING",
            "Arm Stage 2": "TANTALUS_STAGE_2_FLARE.ARM",
            "Ping Stage 2": "TANTALUS_STAGE_2_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.TANTALUS_STAGE_1_FLARE, "Altitude", update_altitude),
            Label(DeviceType.TANTALUS_STAGE_1_FLARE, "MaxAltitude", update_max_altitude, "Max Altitude"),
            Label(DeviceType.TANTALUS_STAGE_1_FLARE, "GPS", update_gps),
            Label(DeviceType.TANTALUS_STAGE_1_FLARE, "State", update_state),
            Label(DeviceType.TANTALUS_STAGE_1_FLARE, "Pressure", update_pressure),
            Label(DeviceType.TANTALUS_STAGE_1_FLARE, "Acceleration", update_acceleration),
            Label(DeviceType.TANTALUS_STAGE_2_FLARE, "Stage2State", update_state, "Stage 2 State"),
            Label(DeviceType.TANTALUS_STAGE_2_FLARE, "DEBUG_APRS_STATE", update_aprs, "DEBUG APRS STATE"),
        ]

    @property
    def expected_devices(self):
        return [
            DeviceType.TANTALUS_STAGE_1_FLARE,
            DeviceType.TANTALUS_STAGE_2_FLARE,
        ]

    @property
    def mapping_devices(self):
        return [
            DeviceType.TANTALUS_STAGE_1_FLARE,
            DeviceType.TANTALUS_STAGE_2_FLARE,
        ]

    @property
    def required_device_versions(self):
        return {
            DeviceType.TANTALUS_STAGE_1_FLARE: REQUIRED_FLARE,
            DeviceType.TANTALUS_STAGE_2_FLARE: REQUIRED_FLARE,
        }

    @property
    def expected_apogee_point(self):
        return None

    @property
    def expected_main_deploy_point(self):
        return None

    def construct_serial_connection(self, com_port: str, baud_rate: int, kiss_address: str):
        return {
            'XBEE_RADIO': SerialConnection(com_port, baud_rate, kiss_address),
        }

    def construct_debug_connection(self, kiss_address: str):
        return {
            'TANTALUS_STAGE_1_CONNECTION': DebugConnection('TANTALUS_STAGE_1_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE],
                                                           stage = 1,
                                                           generate_radio_packets=True,
                                                           kiss_address=kiss_address),

            'TANTALUS_STAGE_2_CONNECTION': DebugConnection('TANTALUS_STAGE_2_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_2_FLARE],
                                                           stage = 2,
                                                           generate_radio_packets=True,
                                                           kiss_address=kiss_address),
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
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
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
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
            VoltageSensor()
        ]

        hw_sim_ignitors_stage_2 = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35),
        ]

        hwsim_stage_2 = HWSim(rocket_sim_stage_2, hw_sim_sensors_stage_2, hw_sim_ignitors_stage_2)

        return {
            'TANTALUS_STAGE_1_CONNECTION': SimConnection("TantalusStage1", "0013A20041678FC0", hwsim_stage_1, stage = 1),
            'TANTALUS_STAGE_2_CONNECTION': SimConnection("TantalusStage2", "0013A20041678FC0", hwsim_stage_2, stage = 2),
        }

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()
