from typing import Iterable
from enum import Enum

from .ignitor_sim import Ignitor
from .sensors.voltage_sensor_sim import VoltageSensor
from .sensors.sensor import Sensor, SensorType, REQUIRED_SENSOR_FLOATS
from .rocket_sim import RocketSim
from util.detail import LOGGER
from util.event_stats import Event
from threading import RLock

SENSOR_READ_EVENT = Event('sensor_read')


class PinModes(Enum):
    INPUT = 0
    OUTPUT = 1


class HWSim:
    def __init__(
            self, rocket_sim: RocketSim, sensors: Iterable[Sensor], ignitors: Iterable[Ignitor],
    ):
        """
        :param sensors: Iterable of all the sensors that the HW contains
        :param ignitors: Iterable of all the ignitors that the HW contains
        :param modes: Dictionary containing pin numbers as keys and associated pin modes as values
        """

        # To protect all HW as SIM is in a different thread from tests, etc.
        self._lock = RLock()

        self._rocket_sim = rocket_sim

        self._pin_modes = {}

        self._sensors = {s.get_type(): s for s in sensors}

        self._voltage_sensor = None
        if SensorType.VOLTAGE in self._sensors:
            self._voltage_sensor = self._sensors[SensorType.VOLTAGE]

        self._ignitors = {i.type: i for i in ignitors}
        self._ignitor_tests = {i.test_pin: i for i in ignitors}
        self._ignitor_reads = {i.read_pin: i for i in ignitors}
        self._ignitor_fires = {i.fire_pin: i for i in ignitors}

        self._paused = False

    def set_pin_mode(self, pin, mode):
        """
        :param pin: Should be a test pin
        :param mode: The mode you want to set the pin to -> 0 for INPUT and 1 for OUTPUT
        """
        with self._lock:
            self._pin_modes[pin] = mode
            LOGGER.debug(f"Pin mode of pin={pin} set to={mode}")

    def get_pin_mode(self, pin):
        """
        :param pin: Should be a test pin
        """
        with self._lock:
            val = self._pin_modes[pin]
            LOGGER.debug(f"Pin mode read from pin={pin} returned value={val}")
            return val

    def digital_write(self, pin, val):
        """
        :param pin: Should be a test pin.
        :param val: True to set high, False to set low
        """
        with self._lock:
            assert self._pin_modes[pin] == PinModes.INPUT
            LOGGER.debug(f"Digital write to pin={pin} with value value={val}")
            if pin in self._ignitor_tests:
                self._ignitor_tests[pin].write(val)
            elif pin in self._ignitor_fires and val:
                self._ignitor_fires[pin].fire()

    def analog_read(self, pin):
        """
        :param pin: Should be a read pin. Don't rely on behaviour if the pin isn't a readable pin.
        """
        with self._lock:
            val = 0
            if pin in self._ignitor_reads:
                val = self._ignitor_reads[pin].read()

            elif self._voltage_sensor:
                if pin == self._voltage_sensor.pin:
                    val = self._voltage_sensor.read()

            LOGGER.debug(f"Analog read from pin={pin} returned value={val}")
            return val

    def sensor_read(self, sensor_type: SensorType) -> tuple:
        """
        :param sensor_type: the sensor to read from
        :return: the sensor data
        """
        with self._lock:
            val = self._sensors[sensor_type].read()

            if len(val) != REQUIRED_SENSOR_FLOATS[sensor_type]:
                raise Exception("Returned values do not correspond to required number of floats.")

            # LOGGER.debug(f"Reading from sensor={sensor_type.name} returned value={val}")
            SENSOR_READ_EVENT.increment()

            return val

    def time_update(self, delta_us: int) -> int:
        """
        :param delta_us: the number of microseconds to shift the clock forward by.
        :return: the current time in milliseconds.
        """
        assert delta_us >= 0

        with self._lock:
            self._rocket_sim.get_clock().add_time(delta_us)
            time_ms = self._rocket_sim.get_clock().get_time_ms()

            return time_ms

    def launch(self) -> None:
        with self._lock:
            self._rocket_sim.launch()

    def deploy_recovery(self) -> None:
        with self._lock:
            self._rocket_sim.deploy_recovery()

    def replace_sensor(self, new_sensor: Sensor):
        with self._lock:
            if new_sensor.get_type() != SensorType.VOLTAGE:
                self._sensors[new_sensor.get_type()] = new_sensor

            else:
                self._voltage_sensor = new_sensor

    def pause(self):
        with self._lock:
            if self._paused:
                raise Exception("HW already paused")

        self._lock.acquire()
        self._paused = True

    def resume(self):
        with self._lock:
            if not self._paused:
                raise Exception("HW is not paused")

        self._lock.release()
        self._paused = False

    def __enter__(self):
        self.pause()

    def __exit__(self, ex, value, tb):
        self.resume()

    def shutdown(self):
        '''
        Shut down any threads and clean-up
        '''
        self._rocket_sim.shutdown()
