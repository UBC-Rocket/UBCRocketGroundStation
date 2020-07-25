import time

import pytest

import main
from DebugConnectionFactory import DebugConnectionFactory


def test_arm_signal(qtbot, capsys):
    factory = DebugConnectionFactory()
    connection = factory.construct()
    main_window = main.MainApp(connection)

    main_window.sendCommand("arm")
    time.sleep(1)
    captured = str(capsys.readouterr())
    if captured.find("b'r' sent to DebugConnection") == -1:
        time.sleep(15)
        captured = str(capsys.readouterr())

    assert captured.find("b'r' sent to DebugConnection") != -1
