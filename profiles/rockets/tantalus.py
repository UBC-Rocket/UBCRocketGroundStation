from ..label import (
    Label,
    update_acceleration,
    update_altitude,
    update_gps,
    update_max_altitude,
    update_pressure,
    update_state,
    update_test_separation,
)
from ..rocket_profile import RocketProfile
from connections.sim.hw_sim import HWSim, DummySensor, SensorType, Ignitor, IgnitorType
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType


class TantalusProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Tantalus"

    @property
    def buttons(self):
        return {
            "Arm Stage 1": "TANTALUS_STAGE_1.ARM",
            "Ping Stage 1": "TANTALUS_STAGE_1.PING"
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.TANTALUS_STAGE_1, "Altitude", update_altitude),
            Label(DeviceType.TANTALUS_STAGE_1, "MaxAltitude", update_max_altitude, "Max Altitude"),
            Label(DeviceType.TANTALUS_STAGE_1, "GPS", update_gps),
            Label(DeviceType.TANTALUS_STAGE_1, "State", update_state),
            Label(DeviceType.TANTALUS_STAGE_1, "Pressure", update_pressure),
            Label(DeviceType.TANTALUS_STAGE_1, "Acceleration", update_acceleration),
            Label(DeviceType.TANTALUS_STAGE_1, "TestSeparation", update_test_separation, "Test Separation"),
        ]

    @property
    def sim_executable_name(self):
        return "TantalusStage1"

    @property
    def mapping_device(self):
        return DeviceType.TANTALUS_STAGE_1

    def construct_hw_sim(self):
        # Assemble HW here

        hw_sim_sensors = [
            DummySensor(SensorType.BAROMETER, (1000, 25)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            DummySensor(SensorType.ACCELEROMETER, (1, 0, 0)),
            DummySensor(SensorType.IMU, (1, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
        ]

        hw_sim_ignitors = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35),
        ]

        return HWSim(hw_sim_sensors, hw_sim_ignitors)

    def construct_app(self, connection):
        return CompApp(connection, self)

    def construct_packet_parser(self, big_endian_ints, big_endian_floats):
        return CompPacketParser(big_endian_ints, big_endian_floats)
