from typing import Iterable
from enum import Enum, auto
from abc import ABC, abstractmethod
from util.detail import LOGGER
from util.event_stats import Event
from threading import RLock

SENSOR_READ_EVENT = Event('sensor_read')

class SensorType(Enum):
    GPS = auto()
    IMU = auto()
    ACCELEROMETER = auto()
    BAROMETER = auto()
    TEMPERATURE = auto()
    THERMOCOUPLE = auto()


REQUIRED_SENSOR_FLOATS = {
    SensorType.GPS: 3,
    SensorType.IMU: 4,
    SensorType.ACCELEROMETER: 3,
    SensorType.BAROMETER: 2,
    SensorType.TEMPERATURE: 1,
    SensorType.THERMOCOUPLE: 1
}

class IgnitorType(Enum):
    MAIN = auto()
    DROGUE = auto()

class Sensor(ABC):

    @abstractmethod
    def read(self) -> tuple:
        # TODO: Ideally we should try to further decouple HW sim from the SIM protocol by finding a way to make the
        #  return values order invariant.
        pass

    @abstractmethod
    def get_type(self) -> SensorType:
        pass


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


class Ignitor:
    """
    Simulates the hardware used for continuity checks.
    """

    # Corresponds to values returned by analogRead.
    CONNECTED = 700  # Continuous
    DISCONNECTED = 600  # Discontinuous
    OFF = 0

    def __init__(self, ignitor_type: IgnitorType, test_pin: int, read_pin: int, fire_pin: int, broken=False):
        """
        In firmware's usage, to test continuity, the test pin is set high, and the voltage level at the read pin is used
        to determine whether the pin is continuous. To fire the pin, the fire pin is set high.

        :param ignitor_type: Purpose of ignitor (aka what's connected to it). Used for asserting in tests
        :param test_pin: Pin number for testing
        :param read_pin: Pin number for reading
        :param fire_pin: Pin number for firing
        :param broken: If true, then it will simulate a used ignitor (and the continuity check should fail)
        """

        self.type = ignitor_type
        self.test_pin = test_pin
        self.read_pin = read_pin
        self.fire_pin = fire_pin

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

class Clock:
    def __init__(self) -> None:
        self._time_us = 0

    def add_time(self, delta_us: float) -> None:
        """
        :param delta_us: number of microseconds to add to the clock.
        """
        self._time_us += delta_us

    def get_time_us(self) -> int:
        """
        :return: the current time in microseconds.
        """
        return self._time_us;

    def get_time_ms(self) -> int:
        """
        :return: the current time in milliseconds.
        """
        return int(self._time_us / 1e3);

class HWSim:
    def __init__(
            self, sensors: Iterable[Sensor], ignitors: Iterable[Ignitor]
    ):
        """
        :param sensors: Iterable of all the sensors that the HW contains
        :param ignitors: Iterable of all the ignitors that the HW contains
        """

        # To protect all HW as SIM is in a different thread from tests, etc.
        self.lock = RLock()

        self.clock = Clock()

        self._sensors = {s.get_type(): s for s in sensors}

        self._ignitors = {i.type: i for i in ignitors}
        self._ignitor_tests = {i.test_pin: i for i in ignitors}
        self._ignitor_reads = {i.read_pin: i for i in ignitors}
        self._ignitor_fires = {i.fire_pin: i for i in ignitors}

    def digital_write(self, pin, val):
        """
        :param pin: Should be a test pin.
        :param val: True to set high, False to set low
        """
        with self.lock:
            LOGGER.debug(f"Digital write to pin={pin} with value value={val}")
            if pin in self._ignitor_tests:
                self._ignitor_tests[pin].write(val)
            elif pin in self._ignitor_fires and val:
                self._ignitor_fires[pin].fire()

    def analog_read(self, pin):
        """
        :param pin: Should be a read pin. Don't rely on behaviour if the pin isn't a readable pin.
        """
        with self.lock:
            val = 0
            if pin in self._ignitor_reads:
                val = self._ignitor_reads[pin].read()

            LOGGER.debug(f"Analog read from pin={pin} returned value={val}")
            return val

    def sensor_read(self, sensor_type: SensorType) -> tuple:
        """
        :param sensor_type: the sensor to read from
        :return: the sensor data
        """
        with self.lock:
            val = self._sensors[sensor_type].read()

            if len(val) != REQUIRED_SENSOR_FLOATS[sensor_type]:
                raise Exception("Returned values do not correspond to required number of floats.")

            #LOGGER.debug(f"Reading from sensor={sensor_type.name} returned value={val}")
            SENSOR_READ_EVENT.increment()

            return val

    def shutdown(self):
        '''
        Shut down any threads and clean-up
        '''
        pass