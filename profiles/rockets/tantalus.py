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

tantalus_labels = [
    Label("Altitude", update_altitude),
    Label("MaxAltitude", update_max_altitude, "Max Altitude"),
    Label("GPS", update_gps),
    Label("State", update_state),
    Label("Pressure", update_pressure),
    Label("Acceleration", update_acceleration),
    Label("TestSeparation", update_test_separation, "Test Separation"),
]

_MAIN_IGN_TEST = 4
_MAIN_IGN_READ = 14
_MAIN_IGN_FIRE = 16
_DROGUE_IGN_TEST = 17
_DROGUE_IGN_READ = 34
_DROGUE_IGN_FIRE = 35


_hw_sim = HWSim(
    [
        (_MAIN_IGN_TEST, _MAIN_IGN_READ, _MAIN_IGN_FIRE),
        (_DROGUE_IGN_TEST, _DROGUE_IGN_READ, _DROGUE_IGN_FIRE),
    ]
)

tantalus = RocketProfile({"Arm": "arm", "Status": "status"}, tantalus_labels, _hw_sim)

