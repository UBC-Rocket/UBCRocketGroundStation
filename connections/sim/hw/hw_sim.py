from typing import Iterable

from .ignitor_sim import Ignitor
from .sensors.sensor import Sensor, SensorType, REQUIRED_SENSOR_FLOATS
from .rocket_sim import RocketSim
from util.detail import LOGGER
from util.event_stats import Event
from threading import RLock

SENSOR_READ_EVENT = Event('sensor_read')

class HWSim:
    def __init__(
            self, rocket_sim: RocketSim, sensors: Iterable[Sensor], ignitors: Iterable[Ignitor]
    ):
        """
        :param sensors: Iterable of all the sensors that the HW contains
        :param ignitors: Iterable of all the ignitors that the HW contains
        """

        # To protect all HW as SIM is in a different thread from tests, etc.
        self.lock = RLock()

        self._rocket_sim = rocket_sim

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

            # LOGGER.debug(f"Reading from sensor={sensor_type.name} returned value={val}")
            SENSOR_READ_EVENT.increment()

            return val

    def time_update(self, delta_us: int) -> int:
        """
        :param delta_us: the number of microseconds to shift the clock forward by.
        :return: the current time in milliseconds.
        """
        assert delta_us >= 0

        with self.lock:
            self._rocket_sim.get_clock().add_time(delta_us)
            time_ms = self._rocket_sim.get_clock().get_time_ms()

            return time_ms

    def launch(self) -> None:
        with self.lock:
            self._rocket_sim.launch()

    def deploy_recovery(self) -> None:
        with self.lock:
            self._rocket_sim.deploy_recovery()

    def replace_sensor(self, new_sensor: Sensor):
        with self.lock:
            self._sensors[new_sensor.get_type()] = new_sensor

    def shutdown(self):
        '''
        Shut down any threads and clean-up
        '''
        pass
