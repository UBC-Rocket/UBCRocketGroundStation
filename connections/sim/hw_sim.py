from typing import Iterable, Tuple


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
    def __init__(self, ignitors: Iterable[Tuple[int, int, int]] = tuple()):
        """
        Implementation note: Default value for ignitors needs to be an immutable iterable.
        :param ignitors: Iterable of 3-tuples containing test, read, and fire pin numbers.
        In firmware's usage, to test continuity, the test pin is set high, and the voltage level at the read pin is used to determine whether the pin is continuous. To fire the pin, the fire pin is set high.
        """
        self.ignitors = []
        self.ignitor_tests = {}
        self.ignitor_reads = {}
        self.ignitor_fires = {}
        for test, read, fire in ignitors:
            ign = IgnitorSim()
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

