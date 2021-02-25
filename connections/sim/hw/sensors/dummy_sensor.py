from connections.sim.hw.sensors.sensor import Sensor, SensorType, REQUIRED_SENSOR_FLOATS


class DummySensor(Sensor):
    """
    Simulates a generic sensor on rocket.
    """

    def __init__(self, sensor_type: SensorType, initial_values: tuple) -> None:
        self.sensor_type = sensor_type
        self._sensor_values = initial_values

        if len(initial_values) != REQUIRED_SENSOR_FLOATS[self.sensor_type]:
            raise Exception("Given values do not correspond to required number of floats.")

    def read(self) -> tuple:
        """
        :brief: return data for sensor
        :return: the sensor data
        """

        return self._sensor_values

    def set_value(self, new_values: tuple):
        """
        :brief: set the values for sensor
        :param new_values: new sensor data. Must match the number of floats required.
        """

        if len(new_values) != REQUIRED_SENSOR_FLOATS[self.sensor_type]:
            raise Exception("Given values do not correspond to required number of floats.")
        self._sensor_values = new_values

    def get_type(self) -> SensorType:
        return self.sensor_type