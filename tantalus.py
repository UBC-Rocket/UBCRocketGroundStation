from label import (Label, update_acceleration, update_altitude, update_gps,
                   update_max_altitude, update_pressure, update_state,
                   update_test_separation)
from rocket_profile import RocketProfile

tantalus_labels = [
    Label("Altitude", update_altitude),
    Label("MaxAltitude", update_max_altitude, "Max Altitude"),
    Label("GPS", update_gps),
    Label("State", update_state),
    Label("Pressure", update_pressure),
    Label("Acceleration", update_acceleration),
    Label("TestSeparation", update_test_separation, "Test Separation"),
]

tantalus = RocketProfile({"Arm": "arm", "Status": "status"}, tantalus_labels)
