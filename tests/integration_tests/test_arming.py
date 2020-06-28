import sys
import time

import pytest

import main

from DebugConnectionFactory import DebugConnectionFactory
from PyQt5 import QtWidgets


def test_arm_signal(qtbot, capsys):
    factory = DebugConnectionFactory()
    connection = factory.construct()
    main_window = main.MainApp(connection)

    time.sleep(1)
    main_window.sendCommand("arm")
    time.sleep(1)
    captured = str(capsys.readouterr())

    assert captured.find("b'r' sent to DebugConnection") != -1
