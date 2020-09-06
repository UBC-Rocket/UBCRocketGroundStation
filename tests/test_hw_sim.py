from connections.sim.hw_sim import HWSim, IgnitorSim


class TestHWSim:
    def test_readwrite(self):
        hw = HWSim([(1, 2, 3), (5, 9, 10)])

        assert hw.analog_read(2) == IgnitorSim.OFF
        assert hw.analog_read(9) == IgnitorSim.OFF

        hw.digital_write(1, True)
        assert hw.analog_read(2) == IgnitorSim.CONNECTED
        assert hw.analog_read(9) == IgnitorSim.OFF
        hw.digital_write(1, False)

        assert hw.analog_read(2) == IgnitorSim.OFF
        assert hw.analog_read(9) == IgnitorSim.OFF

        hw.digital_write(5, True)
        hw.digital_write(7, True)
        assert hw.analog_read(2) == IgnitorSim.OFF
        assert hw.analog_read(9) == IgnitorSim.CONNECTED

    def test_fire(self):
        hw = HWSim([(6, 3, 1)])

        hw.digital_write(1, False)  # Writing false does not fire
        assert hw.analog_read(3) == IgnitorSim.OFF
        hw.digital_write(6, True)
        assert hw.analog_read(3) == IgnitorSim.CONNECTED
        hw.digital_write(6, False)

        hw.digital_write(1, True)  # Fire the pin
        assert hw.analog_read(3) == IgnitorSim.OFF
        hw.digital_write(6, True)
        assert hw.analog_read(3) == IgnitorSim.DISCONNECTED
        hw.digital_write(6, False)

        hw.digital_write(1, False)  # Firing is one-way
        assert hw.analog_read(3) == IgnitorSim.OFF
        hw.digital_write(6, True)
        assert hw.analog_read(3) == IgnitorSim.DISCONNECTED
        hw.digital_write(6, False)
