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


class TantalusProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Tantalus"

    @property
    def buttons(self):
        return {
            "Arm": "arm",
            "Status": "status"
        }

    @property
    def labels(self):
        return [
            Label("Altitude", update_altitude),
            Label("MaxAltitude", update_max_altitude, "Max Altitude"),
            Label("GPS", update_gps),
            Label("State", update_state),
            Label("Pressure", update_pressure),
            Label("Acceleration", update_acceleration),
            Label("TestSeparation", update_test_separation, "Test Separation"),
        ]

    @property
    def sim_executable_name(self):
        return "TantalusStage1"

    def construct_hw_sim(self):
        # Assemble HW here

        hw_sim_sensors = [
            DummySensor(SensorType.BAROMETER, (1000, 25)),
            DummySensor(SensorType.GPS, (12.6, 13.2, 175))
        ]

        hw_sim_ignitors = [
            Ignitor(IgnitorType.MAIN, 4, 14, 16),
            Ignitor(IgnitorType.DROGUE, 17, 34, 35),
        ]

        return HWSim(hw_sim_sensors, hw_sim_ignitors)
