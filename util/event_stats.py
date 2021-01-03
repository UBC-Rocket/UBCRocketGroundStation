import inspect
from threading import Lock, Condition
from util.detail import IS_PYINSTALLER

# Event stats are tracked together so that we can take snapshots at a point in time of all of them
# This can be useful for debugging and profiling
_stats_lock = Lock()
_stats_cv = Condition(_stats_lock)
_stats = dict()

"""

Stats are just counters that can be used to aid with debugging, unit tests, and integration tests. Just like the name 
suggests, they can be placed around the code to count how many times something happened and allows tests/debuggers to 
check if something happened or didnt happen. No actual functionality should depend on this module, only tests. 

"""


class Event:
    def __init__(self, name: str):
        self._name = name
        # Module names are used in conjunction with event name to help prevent event name collision as the code base scales up
        self._module = _get_calling_module()
        self._key = _hash(name, self._module)

    def increment(self, num=1):
        """Increments the counter for the event, indicating that it has occurred.

        :param num: Number by which to increment event counter
        :type num: int
        """

        if _get_calling_module() != self._module:
            raise Exception("Calling module is not the same as the module in which event was defined")

        if type(num) is not int or num < 1:
            raise ValueError("Invalid value for num")

        with _stats_cv:
            if self._key in _stats:
                _stats[self._key] += num
            else:
                _stats[self._key] = num

            _stats_cv.notify_all()

    def wait(self, snapshot, timeout=60, num_expected=1):
        """Waits for the event counter to change compared to snapshot, indicating that it has occurred.

        Difference in event counter is returned so that tests can assert on number of occurrences.

        :param snapshot: A previously captured snapshot to use for comparision
        :type snapshot: dict
        :param timeout: Seconds after which to return
        :type timeout: float
        :param num_expected: Diff expected. Waits until num_expected event occurrences before returning (or timeout)
        :type timeout: int
        :return: difference in event counter
        :rtype: int
        """

        initial_value = snapshot[self._key] if self._key in snapshot else 0

        with _stats_cv:
            def current_value(): return _stats[self._key] if self._key in _stats else 0

            if current_value() < initial_value:
                raise ValueError("Invalid snapshot. Event counter greater than current value.")

            _stats_cv.wait_for(lambda: current_value() - initial_value >= num_expected, timeout=timeout)

            return current_value() - initial_value


def get_event_stats_snapshot():
    """Returns a snapshot of the event stat counters to be compared with.

    A snapshot is needed as a parameter for wait_for_event()

    :return: A copy of the event stat counters
    :rtype: dict
    """

    with _stats_lock:
        return _stats.copy()


def _get_calling_module():
    """Returns the name of the module that called the function that called this function

    :return: Calling module name
    :rtype: str
    """
    frm = inspect.stack()[2] # 2 because we are not interested in two frames up (the previous frame wants to know who called it)

    if not IS_PYINSTALLER:
        module = inspect.getmodule(frm.frame).__name__
    else:
        # getmodule doesnt like pyinstaller, use file name instead
        module = frm.filename

    return module


def _hash(event, module):
    """Hashes event name and module name to create a key for the stats dict

    Module names are used in conjunction with event name to help prevent event name collision as the code base scales up

    :param event: Name of the event
    :type event: str
    :param module: Name of module in which event was incremented
    :type module: str
    :return: Hash of event name and module name
    :rtype: str
    """
    return f"{module}.{event}"
