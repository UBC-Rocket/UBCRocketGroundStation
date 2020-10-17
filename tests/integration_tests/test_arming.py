from connections.debug.debug_connection_factory import DebugConnectionFactory
from connections.debug.debug_connection import ARMED_EVENT
from main_window import main
from profiles.rockets.co_pilot import co_pilot

from util.event_stats import wait_for_event, get_event_stats_snapshot

def test_arm_signal(qtbot, caplog):
    factory = DebugConnectionFactory()
    connection = factory.construct()
    main_window = main.MainApp(connection, co_pilot)

    snapshot = get_event_stats_snapshot()

    main_window.sendCommand("arm")

    num = wait_for_event(snapshot, ARMED_EVENT, 'connections.debug.debug_connection')

    assert num == 1
