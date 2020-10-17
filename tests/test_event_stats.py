import util.event_stats as event_stats
from time import time
import pytest

TEST_EVENT = 'TestEvent'
TEST_MODULE = 'tests.test_event_stats'

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
        snapshot = event_stats.get_event_stats_snapshot()

        event_stats.increment_event_stats(TEST_EVENT)

        ret = event_stats.wait_for_event(snapshot, TEST_EVENT, TEST_MODULE)

        assert ret == 1

        snapshot = event_stats.get_event_stats_snapshot()

        event_stats.increment_event_stats(TEST_EVENT, num=5)

        ret = event_stats.wait_for_event(snapshot, TEST_EVENT, TEST_MODULE)

        assert ret == 5

    def test_bad_snapshot(self):
        event_stats.increment_event_stats(TEST_EVENT)
        snapshot = event_stats.get_event_stats_snapshot()
        snapshot[event_stats._hash(TEST_EVENT, TEST_MODULE)] += 1

        with pytest.raises(ValueError) as ex:
            event_stats.wait_for_event(snapshot, TEST_EVENT, TEST_MODULE)

    def test_module_differentiation(self):
        snapshot = event_stats.get_event_stats_snapshot()

        snapshot[event_stats._hash(TEST_EVENT, 'other_module')] = 5

        event_stats.increment_event_stats(TEST_EVENT)

        ret = event_stats.wait_for_event(snapshot, TEST_EVENT, TEST_MODULE)

        assert ret == 1

    def test_timeout(self):
        snapshot = event_stats.get_event_stats_snapshot()

        start = time()
        ret = event_stats.wait_for_event(snapshot, TEST_EVENT, TEST_MODULE, 0.2)
        end = time()

        assert ret == 0
        assert 0.1 < end - start < 1


