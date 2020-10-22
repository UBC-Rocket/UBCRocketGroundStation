import os
import threading
from time import sleep

from util.event_stats import get_event_stats_snapshot
from util.detail import LOGGER
from main_window.main import LABLES_UPDATED_EVENT, MAP_UPDATED_EVENT

class SelfTest:
    """
    The self test is not intended as a thorough test of all functionality. It just provides an automated method to
    ensure that the GS is able to start without crashing and run basic functionality. Specifically so that CI can
    automatically test that the PyInstaller builds work.
    """

    def __init__(self):
        self.thread = threading.Thread(target=self._run_self_test, daemon=True, name="SelfTestThread")

    def start(self):
        self.thread.start()

    def _run_self_test(self):
        try:
            LOGGER.warning("SELF TEST STARTED")
            snapshot = get_event_stats_snapshot()

            sleep(10)

            # Dont wait, check difference now all at once
            # Add any other common events here
            assert LABLES_UPDATED_EVENT.wait(snapshot, timeout=0) >= 2
            assert MAP_UPDATED_EVENT.wait(snapshot, timeout=0) >= 2

            LOGGER.warning("SELF TEST PASSED")
            os._exit(0)
        except:
            LOGGER.exception("SELF TEST FAILED")
            os._exit(1)
