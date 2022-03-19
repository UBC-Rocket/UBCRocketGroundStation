class Clock:
    def __init__(self) -> None:
        self._time_us = 0

    def add_time(self, delta_us: int) -> None:
        """
        :param delta_us: number of microseconds to add to the clock.
        """
        self._time_us += int(delta_us)

    def get_time_us(self) -> int:
        """
        :return: the current time in microseconds.
        """
        return int(self._time_us)

    def get_time_ms(self) -> int:
        """
        :return: the current time in milliseconds.
        """
        return int(self._time_us / 1e3)