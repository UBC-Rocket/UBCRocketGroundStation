from enum import Enum, auto


class IgnitorType(Enum):
    MAIN = auto()
    DROGUE = auto()


class Ignitor:
    """
    Simulates the hardware used for continuity checks.
    """

    # Corresponds to values returned by analogRead.
    CONNECTED = 700  # Continuous
    DISCONNECTED = 600  # Discontinuous
    OFF = 0

    def __init__(self, ignitor_type: IgnitorType, test_pin: int, read_pin: int, fire_pin: int, broken=False, action_fn=None):
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
        self.action_fn = action_fn

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
        if self.action_fn and self._on_level == self.CONNECTED:
            self.action_fn()

        self._on_level = self.DISCONNECTED
