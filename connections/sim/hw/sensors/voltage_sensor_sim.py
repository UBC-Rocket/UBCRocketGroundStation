from connections.sim.hw.sensors.sensor import *


class VoltageSensor(Sensor):
    """
    Simulates the hardware used for measuring battery voltage.
    """

    # 920mV is the value that gets converted to 11.6V in battery.cpp in FLARE 21899292dc39015570f795ef9e607081aab57e3e
    NOMINAL_VOLTAGE_READ_INPUT = 920
    NOMINAL_VOLTAGE = 11.6

    def __init__(self, pin: int = 36, voltage_read_input: int = NOMINAL_VOLTAGE_READ_INPUT):
        """
        In firmware's usage, to simulate the sensor used to read the battery's voltage
        :param pin The pin whose value will be read from and which will be converted to a voltage level
        """

        self._pin = pin
        self._voltage = voltage_read_input
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
