"""Profile for Sunburst"""

from typing import Optional

from connections.debug.debug_connection import DebugConnection
from connections.serial.serial_connection import SerialConnection
from connections.sim.hw.hw_sim import HWSim
from connections.sim.hw.ignitor_sim import Ignitor, IgnitorType
from connections.sim.hw.rocket_sim import RocketSim
from connections.sim.hw.sensors.dummy_sensor import DummySensor
from connections.sim.hw.sensors.sensor import SensorType
from connections.sim.hw.sensors.sensor_sim import SensorSim
from connections.sim.hw.sensors.voltage_sensor_sim import VoltageSensor #! Do we have this?
from connections.sim.sim_connection import SimConnection
from main_window.competition.comp_app import CompApp
from main_window.competition.comp_packet_parser import CompPacketParser
from main_window.device_manager import DeviceType
from main_window.packet_parser import DEVICE_TYPE_TO_ID
from util.detail import REQUIRED_FLARE
from ..label import (
    Label,
    update_acceleration,
    update_altitude,
    update_gps,
    update_max_altitude,
    update_pressure,
    update_state,
)
from ..mpl_funcs import receive_time_series, receive_map
from ..rocket_profile import RocketProfile, FlightPoint


class SunburstProfile(RocketProfile):
    """Sunburst"""
    @property
    def rocket_name(self):
        return "Sunburst"

    @property
    def buttons(self):
        return {
            "Arm": "SUNBURST_FLARE.ARM",
            "Ping": "SUNBURST_FLARE.PING",
        }

    @property
    def labels(self):
        return [
            Label(DeviceType.SUNBURST_FLARE, "Altitude", update_altitude,
                  map_fn=receive_time_series),
            Label(DeviceType.SUNBURST_FLARE, "MaxAltitude", update_max_altitude, "Max Altitude",
                  map_fn=receive_time_series),
            Label(DeviceType.SUNBURST_FLARE, "GPS", update_gps,
                  map_fn=receive_map),
            Label(DeviceType.SUNBURST_FLARE, "State", update_state,
                  map_fn=receive_time_series),
            Label(DeviceType.SUNBURST_FLARE, "Pressure", update_pressure,
                  map_fn=receive_time_series),
            Label(DeviceType.SUNBURST_FLARE, "Acceleration", update_acceleration,
                  map_fn=receive_time_series),
        ]

    @property
    def expected_devices(self):
        return [DeviceType.SUNBURST_FLARE]

    @property
    def mapping_devices(self):
        return [DeviceType.SUNBURST_FLARE]

    @property
    def required_device_versions(self):
        return {
            DeviceType.SUNBURST_FLARE: REQUIRED_FLARE
        }

    @property
    def expected_apogee_point(self):
        return None
        # return FlightPoint( #! Update this
        #     time=35.9,
        #     time_tolerance=5,
        #     altitude=7603,
        #     altitude_tolerance=30
        # )

    @property
    def expected_main_deploy_point(self):
        return None
        # return FlightPoint( #! Update this
        #     time=514.4,
        #     time_tolerance=5,
        #     altitude=590,
        #     altitude_tolerance=50
        # )

    def construct_serial_connection(self, com_port: str, baud_rate: int, nmea_serial_port: Optional[str], nmea_baud_rate: Optional[int]):
        return {
            'XBEE_RADIO': SerialConnection(com_port, baud_rate, nmea_serial_port=nmea_serial_port, nmea_baud_rate=nmea_baud_rate),
        }

    def construct_debug_connection(self, nmea_serial_port: Optional[str], nmea_baud_rate: Optional[int]):
        return {
            'SUNBURST_FLARE_CONNECTION': DebugConnection('SUNBURST_FLARE_RADIO_ADDRESS',
                                                           DEVICE_TYPE_TO_ID[DeviceType.SUNBURST_FLARE],
                                                           generate_radio_packets=True,
                                                           nmea_serial_port=nmea_serial_port,
                                                           nmea_baud_rate=nmea_baud_rate),
        }

    def construct_sim_connection(self, nmea_serial_port: Optional[str], nmea_baud_rate: Optional[int]):
        # Assemble HW here

        rocket_sim = RocketSim('Sunburst - Dec 8.ork')

        hw_sim_sensors = [  # TODO: Use different values than Tantalus
            SensorSim(SensorType.BAROMETER, rocket_sim, error_stdev=(50, 0.005)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175)),
            SensorSim(SensorType.ACCELEROMETER, rocket_sim),
            DummySensor(SensorType.IMU, (1, 0, 0, 0, 0, 0, 0)),
            DummySensor(SensorType.TEMPERATURE, (20,)),
            # VoltageSensor() #! Do we have this?
        ]

        hw_sim_ignitors = [
            Ignitor(IgnitorType.MAIN, 33, 33, 20, action_fn=rocket_sim.deploy_main), #! Update pin numbers
            Ignitor(IgnitorType.DROGUE, 33, 33, 15, action_fn=rocket_sim.deploy_drogue),
        ]

        hwsim = HWSim(rocket_sim, hw_sim_sensors, hw_sim_ignitors)

        return {
            'SUNBURST_CONNECTION': SimConnection("Sunburst", "0013A20041678FC0", hwsim, nmea_serial_port=nmea_serial_port, nmea_baud_rate=nmea_baud_rate),
        }

    def construct_app(self, connections):
        return CompApp(connections, self)

    def construct_packet_parser(self):
        return CompPacketParser()
