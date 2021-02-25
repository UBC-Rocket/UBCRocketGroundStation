from typing import Iterable, Tuple
import numpy as np

from connections.sim.hw.sensors.sensor import Sensor, SensorType, REQUIRED_SENSOR_FLOATS
from connections.sim.hw.rocket_sim import RocketSim, FlightDataType


class SensorSim(Sensor):
    """
    Simulates a generic sensor on rocket.
    """

    def __init__(self, sensor_type: SensorType, rocket_sim: RocketSim, error_stdev: Iterable[float] = None) -> None:

        if error_stdev is not None and len(error_stdev) != REQUIRED_SENSOR_FLOATS[sensor_type]:
            raise Exception("Length of error_std does not correspond to required number of floats.")

        self.sensor_type = sensor_type
        self.rocket_sim = rocket_sim
        self._error_stdev = error_stdev

    def read(self) -> Tuple[float]:
        """
        :brief: return data for sensor
        :return: the sensor data
        """
        data = {
            SensorType.BAROMETER: self._read_barometer,
            SensorType.ACCELEROMETER: self._read_accelerometer,
        }[self.sensor_type]()

        assert len(data) == REQUIRED_SENSOR_FLOATS[self.sensor_type]

        if self._error_stdev is not None:
            data = [np.random.normal(data[i], self._error_stdev[i]) for i in range(len(data))]

        return tuple(data)

    def get_type(self) -> SensorType:
        return self.sensor_type

    def _read_barometer(self):
        pressure = self.rocket_sim.get_data(FlightDataType.TYPE_AIR_PRESSURE)  # Pa
        temperature = self.rocket_sim.get_data(FlightDataType.TYPE_AIR_TEMPERATURE)  # K

        temperature -= 273.15  # K to C

        return (pressure, temperature)

    def _read_accelerometer(self):
        acceleration_vertical = self.rocket_sim.get_data(FlightDataType.TYPE_ACCELERATION_Z)  # m/s^2

        # TODO: Need to calculate accel based on IMU & rocket orientation
        acceleration_vertical /= 9.81  # m/s^2 to g

        return (acceleration_vertical, 0, 0)
