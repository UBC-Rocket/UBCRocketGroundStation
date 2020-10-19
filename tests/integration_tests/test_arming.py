import time

from connections.debug.debug_connection_factory import DebugConnectionFactory
from main_window import main
from profiles.rockets.co_pilot import co_pilot

from util.detail import init_logger

def test_arm_signal(qtbot, caplog):
    factory = DebugConnectionFactory()
    connection = factory.construct()
    main_window = main.MainApp(connection, co_pilot)

    init_logger()

    main_window.sendCommand("arm")
    time.sleep(1)

    if "b'r' sent to DebugConnection" not in caplog.text:
        time.sleep(15)

    assert "b'r' sent to DebugConnection" in caplog.text
