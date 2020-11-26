import pytest
import logging

from main_window.device_manager import DEVICE_REGISTERED_EVENT
from util.event_stats import get_event_stats_snapshot


@pytest.fixture(scope="function")
def integration_app(caplog):
    app = None

    def construct(profile, connections):
        nonlocal app
        snapshot = get_event_stats_snapshot()
        app = profile.construct_app(connections)
        assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=len(connections)) == len(connections)
        return app

    yield construct

    # ----- Following code is run on cleanup -----

    app.shutdown()

    # Fail test if error message in logs since we catch most exceptions in app
    for when in ("setup", "call"):
        messages = [x.message for x in caplog.get_records(when) if x.levelno == logging.ERROR]
        if messages:
            pytest.fail(f"Errors reported in logs: {messages}")