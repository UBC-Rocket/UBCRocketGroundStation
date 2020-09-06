import math
from typing import TYPE_CHECKING, Callable, Optional, Union

from main_window.subpacket_ids import SubpacketEnum

if TYPE_CHECKING:
    from main_window.main import MainApp


class Label:
    """Front-end data representation for a RocketProfile.

    :param name: The internal name for the label. No spaces; letters only.
    :type name: str
    :param update_func: A function that creates the label's value from a MainApp object.
    :type update_func: Callable[["MainApp"], str]
    :param display_name: The label name that is display on the front-end. Should support most characters.
    :type display_name: str
    """

    def __init__(
        self,
        name: str,
        update_func: Callable[["MainApp"], str],
        display_name: Optional[str] = None,
    ):
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


# TODO: Implement Tantalus test separation label update.
def update_test_separation(main_window: "MainApp") -> str:
    return "Separated"


# TODO: Implement Co-Pilot tank pressure label update.
def update_tank_pressure(main_window: "MainApp") -> str:
    return "10 Pa"


# TODO: Implement Co-Pilot chamber pressure label update.
def update_chamber_pressure(main_window: "MainApp") -> str:
    return "40 Pa"


# TODO: Implement Co-Pilot chamber temperature label update.
def update_chamber_temp(main_window: "MainApp") -> str:
    return "283 K"
