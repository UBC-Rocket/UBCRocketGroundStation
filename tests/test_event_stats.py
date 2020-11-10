import util.event_stats as event_stats
from util.event_stats import Event, get_event_stats_snapshot
from time import time
import pytest

TEST_EVENT = Event('test_event')


class TestEventStats:

    def setup_method(self):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        pass

    def teardown_method(self):
        """ teardown any state that was previously setup with a setup_method
        call.
        """
        # Clear stats
        event_stats._stats = dict()

    def test_general_usage(self):
        snapshot = get_event_stats_snapshot()

        TEST_EVENT.increment()

        ret = TEST_EVENT.wait(snapshot)

        assert ret == 1

        snapshot = get_event_stats_snapshot()

        TEST_EVENT.increment(num=5)

        ret = TEST_EVENT.wait(snapshot)

        assert ret == 5

    def test_bad_snapshot(self):
        TEST_EVENT.increment()
        snapshot = get_event_stats_snapshot()
        snapshot[TEST_EVENT._key] += 1

        with pytest.raises(ValueError) as ex:
            TEST_EVENT.wait(snapshot)

    def test_module_differentiation(self):
        snapshot = get_event_stats_snapshot()

        snapshot[event_stats._hash(TEST_EVENT._name, 'other_module')] = 5

        TEST_EVENT.increment()

        ret = TEST_EVENT.wait(snapshot)

        assert ret == 1

    def test_timeout(self):
        snapshot = get_event_stats_snapshot()

        start = time()
        ret = TEST_EVENT.wait(snapshot, timeout=0.2)
        end = time()

        assert ret == 0
        assert 0.1 < end - start < 0.4

    def test_call_from_other_module(self):
        event = Event('other_event')
        event._module = 'other_module'

        with pytest.raises(Exception) as ex:
            event.increment()