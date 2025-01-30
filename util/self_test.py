import os
import threading
from time import sleep

from util.event_stats import get_event_stats_snapshot
from util.detail import LOGGER
from main_window.competition.comp_app import LABELS_UPDATED_EVENT, MAP_UPDATED_EVENT

class SelfTest:
    """
    The self test is not intended as a thorough test of all functionality. It just provides an automated method to
    ensure that the GS is able to start without crashing and run basic functionality. Specifically so that CI can
    automatically test that the PyInstaller builds work.
    """

    def __init__(self, main_app):
        self.main_app = main_app
        self.thread = threading.Thread(target=self._run_self_test, daemon=True, name="SelfTestThread")

    def start(self):
        self.thread.start()

    def _run_self_test(self):
        try:
            LOGGER.info("SELF TEST STARTED")
            snapshot = get_event_stats_snapshot()

            sleep(20)

            # Dont wait, check difference now all at once
            # Add any other common events here
            assert LABELS_UPDATED_EVENT.wait(snapshot, timeout=0) >= 2
            assert MAP_UPDATED_EVENT.wait(snapshot, timeout=0) >= 2

            LOGGER.info("SELF TEST PASSED")
            ret_code = 0

        except AssertionError:
            LOGGER.exception("SELF TEST FAILED")
            ret_code = 1

        self.main_app.shutdown()
        os._exit(ret_code)
