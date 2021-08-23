from connections.sim.hw.sensors.sensor import *


class VoltageSensor(Sensor):
    """
    Simulates the hardware used for measuring battery voltage.
    """

    NOMINAL_VOLTAGE = 5

    def __init__(self, pin: int):
        """
        In firmware's usage, to simulate the sensor used to read the battery's voltage
        :param pin The pin whose value will be read from and which will be converted to a voltage level
        """

        self._pin = pin

    def read_data(self):
        """
        :brief: Simulate voltage level from output pin.
        :return: Voltage level obtained by mapping analogRead value onto a voltage level.
        :note: currently a dummy implementation that returns a constant value
        """

        return self.NOMINAL_VOLTAGE



