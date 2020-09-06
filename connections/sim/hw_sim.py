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


class HWSim:
    def __init__(self, ignitors: Iterable[Tuple[int, int]]):
        """
        :param ignitors: Iterable of 2-tuples containing test and read pin numbers.
        """
        self.ignitors = []
        self.ignitor_tests = {}
        self.ignitor_reads = {}
        for test, read in ignitors:
            ign = IgnitorSim()
            self.ignitors.append(ign)
            self.ignitor_tests[test] = ign
            self.ignitor_reads[read] = ign

    def digital_write(self, pin, val):
        if pin in self.ignitor_tests:
            self.ignitor_tests[pin].write(val)

    def analog_read(self, pin):
        if pin in self.ignitor_reads:
            return self.ignitor_reads[pin].read()
        return 0

