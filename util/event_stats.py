import inspect
from threading import Lock, Condition

_stats_lock = Lock()
_stats_cv = Condition(_stats_lock)
_stats = dict()


def increment_event_stats(event, num=1):
    """Increments the counter for an event, indicating that it has occurred.

    :param event: Name of the event
    :type event: str
    :param num: Number by which to increment event counter
    :type num: int
    """

    if type(num) is not int or num < 1:
        raise ValueError("Invalid value for num")

    frm = inspect.stack()[1]
    # Module names are used in conjunction with event name to help prevent event name collision as the code base scales up
    module = inspect.getmodule(frm[0]).__name__

    event_hash = _hash(event, module)

    with _stats_cv:
        if event_hash in _stats.keys():
            _stats[event_hash] += num
        else:
            _stats[event_hash] = num

        _stats_cv.notify_all()




def get_event_stats_snapshot():
    """Returns a snapshot of the event stat counters to be compared with.

    A snapshot is needed as a parameter for wait_for_event()

    :return: A copy of the event stat counters
    :rtype: dict
    """

    with _stats_lock:
        return _stats.copy()


def wait_for_event(snapshot, event, module, timeout=60):
    """Increments the counter for an event, indicating that it has occurred.

    Module names are used in conjunction with event name to help prevent event name collision as the code base scales up

    :param snapshot: A previously captured snapshot to use for comparision
    :type snapshot: dict
    :param event: Name of the event
    :type event: str
    :param module: Name of module in which event was incremented
    :type module: str
    :param timeout: Seconds after which to return
    :type timeout: float
    :return: difference in event counter
    :rtype: int
    """

    event_hash = _hash(event, module)

    initial_value = snapshot[event_hash] if event_hash in snapshot.keys() else 0

    with _stats_cv:

        def current_value(): return _stats[event_hash] if event_hash in _stats.keys() else 0

        if current_value() < initial_value:
            raise ValueError("Invalid snapshot. Event counter greater than current value.")

        _stats_cv.wait_for(lambda: current_value() > initial_value, timeout=timeout)

        return current_value() - initial_value



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
