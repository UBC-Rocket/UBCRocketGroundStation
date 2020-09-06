from connections.sim.hw_sim import HWSim, IgnitorSim


class TestHWSim:
    def test_readwrite(self):
        hw = HWSim([(1, 2), (5, 9)])

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

