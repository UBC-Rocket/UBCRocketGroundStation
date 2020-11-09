import pytest
from connections.debug.debug_connection import DebugConnection, ARMED_EVENT
from main_window.main import MainApp, LABLES_UPDATED_EVENT
from profiles.rockets.co_pilot import CoPilotProfile
from connections.debug import radio_packets
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.radio_controller import BULK_SENSOR_EVENT
from main_window.radio_controller import (
    IS_SIM,
    ROCKET_TYPE,
    NONCRITICAL_FAILURE,
    SENSOR_TYPES,
    OTHER_STATUS_TYPES,
)

from util.event_stats import get_event_stats_snapshot

@pytest.fixture(scope="function")
def main_app():
    connection = DebugConnection(generate_radio_packets=False)
    app = MainApp(connection, CoPilotProfile())
    yield app  # Provides app, following code is run on cleanup
    app.shutdown()

def test_arm_signal(qtbot, main_app):
    snapshot = get_event_stats_snapshot()

    main_app.sendCommand("arm")

    num = ARMED_EVENT.wait(snapshot)
    assert num == 1


def test_bulk_sensor_packet(qtbot, main_app):
    connection = main_app.connection

    sensor_inputs = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

    packet = radio_packets.bulk_sensor(*sensor_inputs)

    snapshot = get_event_stats_snapshot()

    with qtbot.waitSignal(
            main_app.ReadThread.sig_received
    ):  # Needed otherwise signals wont process because UI is in same thread
        connection.send_to_rocket(packet)

    num = BULK_SENSOR_EVENT.wait(snapshot)
    assert num == 1

    num = BUNDLE_ADDED_EVENT.wait(snapshot)
    assert num == 1

    def get_val(val):
        return main_app.rocket_data.lastvalue(val.value)

    vals_to_get = (
        SubpacketEnum.CALCULATED_ALTITUDE,
        SubpacketEnum.ACCELERATION_X,
        SubpacketEnum.ACCELERATION_Y,
        SubpacketEnum.ACCELERATION_Z,
        SubpacketEnum.ORIENTATION_1,
        SubpacketEnum.ORIENTATION_2,
        SubpacketEnum.ORIENTATION_3,
        SubpacketEnum.LATITUDE,
        SubpacketEnum.LONGITUDE,
        SubpacketEnum.STATE,
    )
    last_values = tuple(map(get_val, vals_to_get))

    assert sensor_inputs[1:] == last_values

    num = LABLES_UPDATED_EVENT.wait(snapshot)
    assert num == 1

    assert float(main_app.AltitudeLabel.text()) == 2.0
    assert main_app.GPSLabel.text() == "9.0, 10.0"
    assert float(main_app.StateLabel.text()) == 11.0


def test_message_packet(qtbot, main_app, caplog):
    connection = main_app.connection

    packet = radio_packets.message(0, "test_message")

    snapshot = get_event_stats_snapshot()

    connection.send_to_rocket(packet)

    num = BUNDLE_ADDED_EVENT.wait(snapshot)
    assert num == 1

    assert main_app.rocket_data.lastvalue(SubpacketEnum.MESSAGE.value) == "test_message"
    assert "test_message" in caplog.text


def test_config_packet(qtbot, main_app):
    connection = main_app.connection

    packet = radio_packets.config(0, True, 2)

    snapshot = get_event_stats_snapshot()

    connection.send_to_rocket(packet)

    num = BUNDLE_ADDED_EVENT.wait(snapshot)
    assert num == 1

    assert main_app.rocket_data.lastvalue(IS_SIM) == True
    assert main_app.rocket_data.lastvalue(ROCKET_TYPE) == 2


def test_status_ping_packet(qtbot, main_app):
    connection = main_app.connection

    packet = radio_packets.status_ping(
        0, radio_packets.StatusType.CRITICAL_FAILURE, 0xFF, 0xFF, 0xFF, 0xFF
    )

    snapshot = get_event_stats_snapshot()

    connection.send_to_rocket(packet)

    num = BUNDLE_ADDED_EVENT.wait(snapshot)
    assert num == 1

    assert (
            main_app.rocket_data.lastvalue(SubpacketEnum.STATUS_PING.value)
            == NONCRITICAL_FAILURE
    )
    for sensor in SENSOR_TYPES:
        assert main_app.rocket_data.lastvalue(sensor) == 1
    for other in OTHER_STATUS_TYPES:
        assert main_app.rocket_data.lastvalue(other) == 1


def test_clean_shutdown(qtbot):
    connection = DebugConnection(generate_radio_packets=True)
    main_app = MainApp(connection, CoPilotProfile())

    assert main_app.ReadThread.isRunning()
    assert main_app.SendThread.isRunning()
    assert main_app.MappingThread.isRunning()
    assert main_app.rocket_data.autosaveThread.is_alive()
    assert connection.connectionThread.is_alive()

    main_app.shutdown()

    assert main_app.ReadThread.isFinished()
    assert main_app.SendThread.isFinished()
    assert main_app.MappingThread.isFinished()
    assert not main_app.rocket_data.autosaveThread.is_alive()
    assert not connection.connectionThread.is_alive()
