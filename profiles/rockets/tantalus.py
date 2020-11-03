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
from connections.sim.hw_sim import HWSim

_MAIN_IGN_TEST = 4
_MAIN_IGN_READ = 14
_MAIN_IGN_FIRE = 16
_DROGUE_IGN_TEST = 17
_DROGUE_IGN_READ = 34
_DROGUE_IGN_FIRE = 35

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

    def construct_hw_sim(self):
        # Assemble HW here

        hw_sim_ignitors = [
            (_MAIN_IGN_TEST, _MAIN_IGN_READ, _MAIN_IGN_FIRE),
            (_DROGUE_IGN_TEST, _DROGUE_IGN_READ, _DROGUE_IGN_FIRE),
        ]

        return HWSim(hw_sim_ignitors)
