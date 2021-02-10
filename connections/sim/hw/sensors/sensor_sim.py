from typing import Iterable

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

    def __init__(self, sensor_type: SensorType, rocket_sim: RocketSim, data_types: Iterable[FlightDataType]) -> None:
        self.sensor_type = sensor_type
        self.rocket_sim = rocket_sim
        self._data_types = data_types

        if len(data_types) != REQUIRED_SENSOR_FLOATS[self.sensor_type]:
            raise Exception("Given values do not correspond to required number of floats.")

    def read(self) -> tuple:
        """
        :brief: return data for sensor
        :return: the sensor data
        """
        return tuple(CONVERT_FROM_SI_UNITS[x](self.rocket_sim.get_data(x)) for x in self._data_types)

    def get_type(self) -> SensorType:
        return self.sensor_type
