import math
from typing import TYPE_CHECKING, Callable, Optional, Union
from main_window.subpacket_ids import SubpacketEnum
from main_window.rocket_data import RocketData
from main_window.device_manager import DeviceType


class Label:
    """Front-end data representation for a RocketProfile.

    :param name: The internal name for the label. No spaces; letters only.
    :type name: str
    :param update_func: A function that creates the label's value from a MainApp object.
    :type update_func: Callable[[RocketData], str]
    :param display_name: The label name that is display on the front-end. Should support most characters.
    :type display_name: str
    """

    def __init__(
            self,
            device: DeviceType,
            name: str,
            update_func: Callable[[RocketData, DeviceType], str],
            display_name: Optional[str] = None,
    ):
        self.device = device
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.update_fn = update_func  # Must support last_value_by_device returning None

    def update(self, rocket_data: RocketData):
        return self.update_fn(rocket_data, self.device)


def update_altitude(rocket_data: RocketData, device: DeviceType) -> str:
    return str(rocket_data.last_value_by_device(device, SubpacketEnum.CALCULATED_ALTITUDE.value))


def update_max_altitude(rocket_data: RocketData, device: DeviceType) -> str:
    return str(rocket_data.highest_altitude)


def update_gps(rocket_data: RocketData, device: DeviceType) -> str:
    latitude = rocket_data.last_value_by_device(device, SubpacketEnum.LATITUDE.value)
    longitude = rocket_data.last_value_by_device(device, SubpacketEnum.LONGITUDE.value)
    return str(latitude) + ", " + str(longitude)


def update_state(rocket_data: RocketData, device: DeviceType) -> str:
    return str(rocket_data.last_value_by_device(device, SubpacketEnum.STATE.value))


def update_pressure(rocket_data: RocketData, device: DeviceType) -> str:
    return str(rocket_data.last_value_by_device(device, SubpacketEnum.PRESSURE.value))


def update_acceleration(rocket_data: RocketData, device: DeviceType) -> str:
    def nonezero(x: Union[float, None]) -> float:
        return 0 if x is None else x  # To support lastvalue returning None

    accel = math.sqrt(
        nonezero(rocket_data.last_value_by_device(device, SubpacketEnum.ACCELERATION_X.value)) ** 2
        + nonezero(rocket_data.last_value_by_device(device, SubpacketEnum.ACCELERATION_Y.value)) ** 2
        + nonezero(rocket_data.last_value_by_device(device, SubpacketEnum.ACCELERATION_Z.value)) ** 2
    )
    return str(accel)


# TODO: Implement Tantalus test separation label update.
def update_test_separation(rocket_data: RocketData, device: DeviceType) -> str:
    return "Separated"


# TODO: Implement Co-Pilot tank pressure label update.
def update_tank_pressure(rocket_data: RocketData, device: DeviceType) -> str:
    return "10 Pa"


# TODO: Implement Co-Pilot chamber pressure label update.
def update_chamber_pressure(rocket_data: RocketData, device: DeviceType) -> str:
    return "40 Pa"


# TODO: Implement Co-Pilot chamber temperature label update.
def update_chamber_temp(rocket_data: RocketData, device: DeviceType) -> str:
    return "283 K"
