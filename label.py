import math
from typing import TYPE_CHECKING, Callable, Optional, Union

from SubpacketIDs import SubpacketEnum

if TYPE_CHECKING:
    from main import MainApp


class Label:
    def __init__(self, name: str, update_func: Callable[["MainApp"], str], display_name: Optional[str] = None):
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.update = update_func


def update_altitude(main_window: "MainApp") -> str:
    return str(main_window.data.lastvalue(SubpacketEnum.CALCULATED_ALTITUDE.value))


def update_max_altitude(main_window: "MainApp") -> str:
    return str(main_window.data.highest_altitude)


def update_gps(main_window: "MainApp") -> str:
    latitude = main_window.data.lastvalue(SubpacketEnum.LATITUDE.value)
    longitude = main_window.data.lastvalue(SubpacketEnum.LONGITUDE.value)
    return str(latitude) + ", " + str(longitude)


def update_state(main_window: "MainApp") -> str:
    return str(main_window.data.lastvalue(SubpacketEnum.STATE.value))


def update_pressure(main_window: "MainApp") -> str:
    return str(main_window.data.lastvalue(SubpacketEnum.PRESSURE.value))


def update_acceleration(main_window: "MainApp") -> str:
    def nonezero(x: Union[float, None]) -> float:
        return 0 if x is None else x

    accel = math.sqrt(
        nonezero(main_window.data.lastvalue(SubpacketEnum.ACCELERATION_X.value)) ** 2
        + nonezero(main_window.data.lastvalue(SubpacketEnum.ACCELERATION_Y.value)) ** 2
        + nonezero(main_window.data.lastvalue(SubpacketEnum.ACCELERATION_Z.value)) ** 2
    )
    return str(accel)


default_labels = [
    Label("Altitude", update_altitude),
    Label("MaxAltitude", update_max_altitude, "Max Altitude"),
    Label("GPS", update_gps),
    Label("State", update_state),
    Label("Pressure", update_pressure),
    Label("Acceleration", update_acceleration),
]
