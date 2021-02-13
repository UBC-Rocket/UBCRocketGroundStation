from typing import Iterable
import numpy as np

from connections.sim.hw.sensors.sensor import Sensor, SensorType, REQUIRED_SENSOR_FLOATS
from connections.sim.hw.rocket_sim import RocketSim, FlightDataType

# RocketSim/OpenRocket uses pure SI units, sensors do not.
CONVERT_FROM_SI_UNITS = {
    FlightDataType.TYPE_AIR_PRESSURE: lambda x: x / 100,  # Pa to mbar
    FlightDataType.TYPE_AIR_TEMPERATURE: lambda x: x - 273.15,  # K to C
    FlightDataType.TYPE_ACCELERATION_Z: lambda x: x / 9.81,  # m/s^2 to g
}

class SensorSim(Sensor):
    """
    Simulates a generic sensor on rocket.
    """

    def __init__(self, sensor_type: SensorType, rocket_sim: RocketSim, data_types: Iterable[FlightDataType], error_stdev: Iterable[float]=None) -> None:
        if len(data_types) != REQUIRED_SENSOR_FLOATS[sensor_type]:
            raise Exception("Length of data_types does not correspond to required number of floats.")

        if error_stdev is not None and len(error_stdev) != REQUIRED_SENSOR_FLOATS[sensor_type]:
            raise Exception("Length of error_std does not correspond to required number of floats.")

        self.sensor_type = sensor_type
        self.rocket_sim = rocket_sim
        self._data_types = data_types
        self._error_stdev = error_stdev

    def read(self) -> tuple:
        """
        :brief: return data for sensor
        :return: the sensor data
        """
        data = [CONVERT_FROM_SI_UNITS[x](self.rocket_sim.get_data(x)) for x in self._data_types]

        if self._error_stdev is not None:
            data = [np.random.normal(data[i], self._error_stdev[i]) for i in range(len(data))]

        return tuple(data)

    def get_type(self) -> SensorType:
        return self.sensor_type
