from connections.sim.hw.sensors.sensor import *


class VoltageSensor(Sensor):
    """
    Simulates the hardware used for measuring battery voltage.
    """

    NOMINAL_VOLTAGE_READ_INPUT = 920  # 920mV is the value that gets converted to 11.6V in battery.cpp in FLARE
    NOMINAL_VOLTAGE = 11.6

    def __init__(self, pin: int = 36):
        """
        In firmware's usage, to simulate the sensor used to read the battery's voltage
        :param pin The pin whose value will be read from and which will be converted to a voltage level
        """

        self._pin = pin
        self._voltage = self.NOMINAL_VOLTAGE_READ_INPUT
        self.sensor_type = SensorType.VOLTAGE

    def read(self):
        """
        :brief: Simulate voltage level from output pin.
        :return: Voltage level obtained by mapping analogRead value onto a voltage level.
        :note: currently a dummy implementation that returns a constant value
        """

        return self._voltage

    @property
    def pin(self):
        return self._pin

    def get_type(self) -> SensorType:
        return self.sensor_type
