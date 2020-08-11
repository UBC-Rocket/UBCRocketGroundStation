import math
from typing import Union

from rocket_profile import RocketProfile, default_labels
from SubpacketIDs import SubpacketEnum


class Tantalus(RocketProfile):
    @staticmethod
    def update_altitude(main_window) -> str:
        return str(main_window.data.lastvalue(SubpacketEnum.CALCULATED_ALTITUDE.value))

    @staticmethod
    def update_max_altitude(main_window) -> str:
        return str(main_window.data.highest_altitude)

    @staticmethod
    def update_gps(main_window) -> str:
        latitude = main_window.data.lastvalue(SubpacketEnum.LATITUDE.value)
        longitude = main_window.data.lastvalue(SubpacketEnum.LONGITUDE.value)
        return str(latitude) + ", " + str(longitude)

    @staticmethod
    def update_state(main_window) -> str:
        return str(main_window.data.lastvalue(SubpacketEnum.STATE.value))

    @staticmethod
    def update_pressure(main_window) -> str:
        return str(main_window.data.lastvalue(SubpacketEnum.PRESSURE.value))

    @staticmethod
    def update_acceleration(main_window) -> str:
        def nonezero(x: Union[float, None]) -> float:
            return 0 if x is None else x

        accel = math.sqrt(
            nonezero(main_window.data.lastvalue(SubpacketEnum.ACCELERATION_X.value))
            ** 2
            + nonezero(main_window.data.lastvalue(SubpacketEnum.ACCELERATION_Y.value))
            ** 2
            + nonezero(main_window.data.lastvalue(SubpacketEnum.ACCELERATION_Z.value))
            ** 2
        )
        return str(accel)


tantalus = Tantalus({"Arm": "arm", "Status": "status"}, {**default_labels})
