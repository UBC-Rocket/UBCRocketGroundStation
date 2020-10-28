from ..label import (Label, update_acceleration, update_altitude,
                     update_chamber_pressure, update_chamber_temp, update_gps,
                     update_max_altitude, update_pressure, update_state,
                     update_tank_pressure)
from ..rocket_profile import RocketProfile

cp_labels = [
    Label("Altitude", update_altitude),
    Label("MaxAltitude", update_max_altitude, "Max Altitude"),
    Label("GPS", update_gps),
    Label("State", update_state),
    Label("Pressure", update_pressure),
    Label("Acceleration", update_acceleration),
    Label("TankPressure", update_tank_pressure, "Tank Pressure"),
    Label("ChamberPressure", update_chamber_pressure, "Chamber Pressure"),
    Label("ChamberTemp", update_chamber_temp, "Chamber Temperature"),
]

whistler_blackcomb = RocketProfile(
    {"Arm": "arm", "Halo": "halo", "Data": "data", "Status": "status"}, cp_labels
)
