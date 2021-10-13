from connections.sim.hw.sensors.sensor import *


class VoltageSensor(Sensor):
    """
    Simulates the hardware used for measuring battery voltage.
    """

    NOMINAL_VOLTAGE = 11.6

    def __init__(self, pin: int):
        """
        In firmware's usage, to simulate the sensor used to read the battery's voltage
        :param pin The pin whose value will be read from and which will be converted to a voltage level
        """

        self._pin = pin
        self._last_val = 0

    def read(self):
        """
        :brief: Simulate voltage level from output pin.
        :return: Voltage level obtained by mapping analogRead value onto a voltage level.
        :note: currently a dummy implementation that returns a constant value
        """
        self._last_val = self.NOMINAL_VOLTAGE

        return self._last_val

    @property
    def pin(self):
        return self._pin

    @property
    def last_val(self):
        return self._last_val

    def get_type(self) -> SensorType:
        return SensorType.VOLTAGE

