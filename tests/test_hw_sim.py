from unittest.mock import MagicMock

from connections.sim.hw.hw_sim import HWSim, PinModes
from connections.sim.hw.sensors.sensor import SensorType
from connections.sim.hw.sensors.dummy_sensor import DummySensor
from connections.sim.hw.ignitor_sim import Ignitor, IgnitorType
from connections.sim.hw.clock_sim import Clock


def ignitor_test(hw, test, read):
    """Utility function - does continuity check like FW would"""
    hw.digital_write(test, True)
    result = hw.analog_read(read)
    hw.digital_write(test, False)
    return result


class TestHWSim:
    def test_pin_mode(self):
        hw = HWSim(None, [], [])
        hw.set_pin_mode(1, PinModes.OUTPUT)
        hw.set_pin_mode(3, PinModes.INPUT)
        hw.set_pin_mode(2, PinModes.OUTPUT)

        assert hw.get_pin_mode(1) == PinModes.OUTPUT
        assert hw.get_pin_mode(3) == PinModes.INPUT
        assert hw.get_pin_mode(2) == PinModes.OUTPUT

    def test_ignitor_readwrite(self):
        hw = HWSim(None, [], [Ignitor(IgnitorType.MAIN, 1, 2, 3), Ignitor(IgnitorType.DROGUE, 5, 9, 10)])

        hw.set_pin_mode(2, PinModes.OUTPUT)
        hw.set_pin_mode(9, PinModes.OUTPUT)
        assert hw.analog_read(2) == Ignitor.OFF
        assert hw.analog_read(9) == Ignitor.OFF

        hw.set_pin_mode(1, PinModes.INPUT)
        hw.digital_write(1, True)
        assert hw.analog_read(2) == Ignitor.CONNECTED
        assert hw.analog_read(9) == Ignitor.OFF
        hw.digital_write(1, False)

        assert hw.analog_read(2) == Ignitor.OFF
        assert hw.analog_read(9) == Ignitor.OFF

        hw.set_pin_mode(5, PinModes.INPUT)
        hw.set_pin_mode(7, PinModes.INPUT)
        hw.digital_write(5, True)
        hw.digital_write(7, True)
        assert hw.analog_read(2) == Ignitor.OFF
        assert hw.analog_read(9) == Ignitor.CONNECTED

    def test_ignitor_fire(self):
        hw = HWSim(None, [], [Ignitor(IgnitorType.MAIN, 6, 3, 1)])

        hw.set_pin_mode(1, PinModes.INPUT)
        hw.set_pin_mode(3, PinModes.OUTPUT)
        hw.set_pin_mode(6, PinModes.INPUT)
        hw.digital_write(1, False)  # Writing false does not fire
        assert hw.analog_read(3) == Ignitor.OFF
        hw.digital_write(6, True)
        assert hw.analog_read(3) == Ignitor.CONNECTED
        hw.digital_write(6, False)

        hw.digital_write(1, True)  # Fire the pin
        assert hw.analog_read(3) == Ignitor.OFF
        hw.digital_write(6, True)
        assert hw.analog_read(3) == Ignitor.DISCONNECTED
        hw.digital_write(6, False)

        hw.digital_write(1, False)  # Firing is one-way
        assert hw.analog_read(3) == Ignitor.OFF
        hw.digital_write(6, True)
        assert hw.analog_read(3) == Ignitor.DISCONNECTED
        hw.digital_write(6, False)

    def test_ignitor_broken(self):
        hw = HWSim(None, [], [Ignitor(IgnitorType.MAIN, 1, 2, 3, broken=True), Ignitor(IgnitorType.DROGUE, 4, 5, 6, broken=True)])

        hw.set_pin_mode(1, PinModes.INPUT)
        hw.set_pin_mode(2, PinModes.OUTPUT)
        hw.set_pin_mode(3, PinModes.INPUT)
        hw.set_pin_mode(4, PinModes.INPUT)
        hw.set_pin_mode(5, PinModes.OUTPUT)
        hw.set_pin_mode(6, PinModes.INPUT)

        assert ignitor_test(hw, 1, 2) == Ignitor.DISCONNECTED
        assert ignitor_test(hw, 4, 5) == Ignitor.DISCONNECTED

        hw = HWSim(None, [], [Ignitor(IgnitorType.MAIN, 1, 2, 3, broken=True), Ignitor(IgnitorType.DROGUE, 4, 5, 6, broken=False)])

        hw.set_pin_mode(1, PinModes.INPUT)
        hw.set_pin_mode(2, PinModes.OUTPUT)
        hw.set_pin_mode(3, PinModes.INPUT)
        hw.set_pin_mode(4, PinModes.INPUT)
        hw.set_pin_mode(5, PinModes.OUTPUT)
        hw.set_pin_mode(6, PinModes.INPUT)

        assert ignitor_test(hw, 1, 2) == Ignitor.DISCONNECTED
        assert ignitor_test(hw, 4, 5) == Ignitor.CONNECTED

        hw.digital_write(6, True)
        assert ignitor_test(hw, 4, 5) == Ignitor.DISCONNECTED

    def test_sensor_read(self):
        GPS_DATA = (1, 2, 3)
        BARO_DATA = (4, 5)

        GPS = DummySensor(SensorType.GPS, GPS_DATA)
        BARO = DummySensor(SensorType.BAROMETER, BARO_DATA)

        hw = HWSim(None, [GPS, BARO], [])

        assert hw.sensor_read(SensorType.GPS) == GPS_DATA
        assert hw.sensor_read(SensorType.BAROMETER) == BARO_DATA

        GPS_DATA = (11, 12, 13)
        BARO_DATA = (14, 15)

        GPS.set_value(GPS_DATA)
        BARO.set_value(BARO_DATA)

        assert hw.sensor_read(SensorType.GPS) == GPS_DATA
        assert hw.sensor_read(SensorType.BAROMETER) == BARO_DATA

    def test_clock(self):
        clock = Clock()
        rocket_sim = MagicMock()
        rocket_sim.get_clock = MagicMock(return_value=clock)

        hw = HWSim(rocket_sim, [], [])

        assert clock.get_time_ms() == 0
        assert clock.get_time_us() == 0

        assert hw.time_update(1000) == 1
        assert hw.time_update(1900) == 2
        assert hw.time_update(100) == 3
