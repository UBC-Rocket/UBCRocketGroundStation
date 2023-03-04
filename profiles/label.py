import math
from typing import TYPE_CHECKING, Callable, Optional, Union
from main_window.main_app import MainApp
from main_window.data_entry_id import DataEntryIds, DataEntryValues
from main_window.rocket_data import RocketData
from main_window.device_manager import DeviceType

VALUE_NOT_AVAILABLE = "N/A"


class Label:
    """Front-end data representation for a RocketProfile.

    :param name: The internal name for the label. No spaces; letters only.
    :type name: str
    :param update_func: A function that creates the label's value from a MainApp object.
    :type update_func: Callable[[RocketData], str]
    :param display_name: The label name that is display on the front-end.
                         Should support most characters.
    :type display_name: str
    """

    def __init__(
            self,
            device: DeviceType,
            name: str,
            update_func: Callable[[RocketData, DeviceType], str],
            display_name: Optional[str] = None,
            map_fn: Optional[Callable[[MainApp], None]] = None,
    ):
        self.device = device
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.update_fn = update_func  # Must support last_value_by_device returning None
        self.map_fn = map_fn

    def update(self, rocket_data: RocketData):
        return self.update_fn(rocket_data, self.device)

    def update_map(self, main_app: MainApp):
        if self.map_fn is not None:
            self.map_fn(main_app)


def update_altitude(rocket_data: RocketData, device: DeviceType) -> str:
    altitude = rocket_data.last_value_by_device(
        device, DataEntryIds.CALCULATED_ALTITUDE
    )
    if altitude is not None:
        return f"{altitude:.2f} m"
    else:
        return VALUE_NOT_AVAILABLE


def update_max_altitude(rocket_data: RocketData, device: DeviceType) -> str:
    altitude = rocket_data.highest_altitude_by_device(device)
    if altitude is not None:
        return f"{altitude:.2f} m"
    else:
        return VALUE_NOT_AVAILABLE


def update_gps(rocket_data: RocketData, device: DeviceType) -> str:
    latitude = rocket_data.last_value_by_device(device, DataEntryIds.LATITUDE)
    longitude = rocket_data.last_value_by_device(device, DataEntryIds.LONGITUDE)
    if latitude is not None and longitude is not None:
        return f"{latitude:.5f}\xb0, {longitude:.5f}\xb0"
    else:
        return VALUE_NOT_AVAILABLE


def update_state(rocket_data: RocketData, device: DeviceType) -> str:
    state: Union[DataEntryValues, None] = rocket_data.last_value_by_device(
                                            device, DataEntryIds.STATE)
    if state is not None:
        return state.name
    else:
        return VALUE_NOT_AVAILABLE


def update_pressure(rocket_data: RocketData, device: DeviceType) -> str:
    pressure = rocket_data.last_value_by_device(device, DataEntryIds.PRESSURE)
    if pressure is not None:
        return f"{pressure:.2f} mbar"
    else:
        return VALUE_NOT_AVAILABLE


def update_acceleration(rocket_data: RocketData, device: DeviceType) -> str:
    x = rocket_data.last_value_by_device(device, DataEntryIds.ACCELERATION_X)
    y = rocket_data.last_value_by_device(device, DataEntryIds.ACCELERATION_Y)
    z = rocket_data.last_value_by_device(device, DataEntryIds.ACCELERATION_Z)

    if all([val is not None for val in (x, y, z)]):
        accel = math.sqrt(x ** 2 + y ** 2 + z ** 2)
        return f"{accel:.2f} g"
    else:
        return VALUE_NOT_AVAILABLE


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
