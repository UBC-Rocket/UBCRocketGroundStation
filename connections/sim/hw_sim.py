from typing import Iterable, Tuple
from itertools import repeat
from enum import Enum

class SensorIDs(Enum):
    """
    Sensor IDs - Sensor ID specifications
    format (sensor id, number of data floats)
    """
    GPS = 0x00, 3
    IMU = 0x01, 4
    ACCELEROMETER = 0x02, 3
    BAROMETER = 0x03, 2
    TEMPERATURE = 0x04, 1
    THERMOCOUPLE = 0x05, 1

class SensorSim:
    """
    Simulates all sensors on rocket.
    """

    def __init__(self, sensor: SensorIDs, initial_values: tuple) -> None:
        self.sensor_id = sensor.value[0]
        self.num_floats = sensor.value[1]
        if len(initial_values) != self.num_floats:
            raise Exception("Given values do not correspond to required number of floats.")
        self._sensor_values = initial_values

    def read(self) -> tuple:
        """
        :brief: return data for sensor
        :return: the sensor data
        """
        return self._sensor_values

    def write(self, new_values: tuple):
        """
        :brief: write values for specific sensor
        :param new_values: new sensor data. Much match the number of
        floats required.
        """
        if len(new_values) != self.num_floats:
            raise Exception("Given values do not correspond to required number of floats.")
        self._sensor_values = new_values

class IgnitorSim:
    """
    Simulates the hardware used for continuity checks.
    """

    # Corresponds to values returned by analogRead.
    CONNECTED = 700  # Continuous
    DISCONNECTED = 600  # Discontinuous
    OFF = 0

    def __init__(self, broken=False):
        """
        :param broken: If true, then it will simulate a used ignitor (and the continuity check should fail)
        """
        self._on = False
        if broken:
            self._on_level = self.DISCONNECTED
        else:
            self._on_level = self.CONNECTED

    def write(self, val):
        """
        :brief: Write value to test pin, in manner of digitalWrite.
        :param val: True (or castable to true) corresponds to a continuity test being done, and False indicates testing is complete.
        """
        if val:
            self._on = True
        else:
            self._on = False

    def read(self):
        """
        :brief: Simulate analogRead from output pin.
        :return: Expected output.
        """
        if self._on:
            return self._on_level
        else:
            return self.OFF

    def fire(self):
        self._on_level = self.DISCONNECTED


class HWSim:
    def __init__(
        self, ignitors: Iterable[Tuple[int, int, int]] = tuple(), broken=False
    ):

        self.sensors = {}
        
        self.barometer = SensorSim(SensorIDs.BAROMETER, (1000, 25))
        self.gps = SensorSim(SensorIDs.GPS, (12.6, 13.2, 175))

        self.sensors[self.barometer.sensor_id] = self.barometer
        self.sensors[self.gps.sensor_id] = self.gps

        
        """
        Implementation note: Default value for ignitors needs to be an immutable iterable.
        :param ignitors: Iterable of 3-tuples containing test, read, and fire pin numbers.
        In firmware's usage, to test continuity, the test pin is set high, and the voltage level at the read pin is used to determine whether the pin is continuous. To fire the pin, the fire pin is set high.
        :param broken: If boolean, indicates whether all ignitors are broken. If iterable, should be the same length as ``ignitors``, and specify in order which ignitor is broken.
        """
        self.ignitors = []
        self.ignitor_tests = {}
        self.ignitor_reads = {}
        self.ignitor_fires = {}
        if isinstance(broken, bool):
            broken = repeat(broken)
        for (test, read, fire), broke in zip(ignitors, broken):
            ign = IgnitorSim(broke)
            self.ignitors.append(ign)
            self.ignitor_tests[test] = ign
            self.ignitor_reads[read] = ign
            self.ignitor_fires[fire] = ign

    def digital_write(self, pin, val):
        """
        :param pin: Should be a test pin.
        :param val: True to set high, False to set low
        """
        if pin in self.ignitor_tests:
            self.ignitor_tests[pin].write(val)
        elif pin in self.ignitor_fires and val:
            self.ignitor_fires[pin].fire()

    def analog_read(self, pin):
        """
        :param pin: Should be a read pin. Don't rely on behaviour if the pin isn't a readable pin.
        """
        if pin in self.ignitor_reads:
            return self.ignitor_reads[pin].read()
        return 0

    def sensor_read(self, sensor_id: int) -> tuple:
        """
        :param sensor_id: the sensor ID to read from
        :return: the sensor data
        """
        return self.sensors[sensor_id].read()

