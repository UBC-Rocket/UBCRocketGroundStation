from connections.sim.hw.sensors.sensor import *


class VoltageSensor(Sensor):
    """
    Simulates the hardware used for measuring battery voltage.
    """

    # The ADC level of 920 gets converted to 11.6V in battery.cpp in FLARE 21899292dc39015570f795ef9e607081aab57e3e
    NOMINAL_ADC_LEVEL = 920
    NOMINAL_BATTERY_VOLTAGE = 11.6

    def __init__(self, pin: int = 23, dummy_adc_level: int = NOMINAL_ADC_LEVEL):
        """
        In firmware's usage, to simulate the sensor used to read the battery's voltage
        :param pin: The pin whose value (raw ADC level between 0 and 1023) will be read from
        :param dummy_adc_level: The ADC level which gets converted to pin voltage then battery voltage during a read
        """

        self._pin = pin
        self._adc_level = dummy_adc_level
        self.sensor_type = SensorType.VOLTAGE

    def read(self):
        """
        :brief: Simulate ADC level from output pin
        """

        return self._adc_level

    @property
    def pin(self):
        return self._pin

    def get_type(self) -> SensorType:
        return self.sensor_type
