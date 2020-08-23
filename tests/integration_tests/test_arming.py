import time

import main
from connections.debug.debug_connection_factory import DebugConnectionFactory
from profiles.rockets.co_pilot import co_pilot


def test_arm_signal(qtbot, capsys):
    factory = DebugConnectionFactory()
    connection = factory.construct()
    main_window = main.MainApp(connection, co_pilot)

    main_window.sendCommand("arm")
    time.sleep(1)
    captured = str(capsys.readouterr())
    if captured.find("b'r' sent to DebugConnection") == -1:
        time.sleep(15)
        captured = str(capsys.readouterr())

    assert captured.find("b'r' sent to DebugConnection") != -1
