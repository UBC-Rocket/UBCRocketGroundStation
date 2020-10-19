from connections.debug.debug_connection import DebugConnection, ARMED_EVENT
from main_window.main import MainApp, LABLES_UPDATED_EVENT
from profiles.rockets.co_pilot import co_pilot
import connections.debug.radio_packets as radio_packets
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.radio_controller import IS_SIM, ROCKET_TYPE, NONCRITICAL_FAILURE, SENSOR_TYPES, OTHER_STATUS_TYPES

from util.event_stats import wait_for_event, get_event_stats_snapshot

def test_arm_signal(qtbot):
    connection = DebugConnection(generate_radio_packets=False)
    main_window = MainApp(connection, co_pilot)

    snapshot = get_event_stats_snapshot()

    main_window.sendCommand("arm")

    num = wait_for_event(snapshot, ARMED_EVENT, 'connections.debug.debug_connection')

    assert num == 1

def test_bulk_sensor_packet(qtbot):
    connection = DebugConnection(generate_radio_packets=False)
    main_window = MainApp(connection, co_pilot)

    packet = radio_packets.bulk_sensor(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

    snapshot = get_event_stats_snapshot()

    with qtbot.waitSignal(main_window.ReadThread.sig_received): # Needed otherwise signals wont process because UI is in same thread
        connection.send_to_rocket(packet)

    num = wait_for_event(snapshot, BUNDLE_ADDED_EVENT, 'main_window.rocket_data')
    assert num == 1
    assert main_window.data.lastvalue(SubpacketEnum.CALCULATED_ALTITUDE.value) == 2
    assert main_window.data.lastvalue(SubpacketEnum.ACCELERATION_X.value) == 3
    assert main_window.data.lastvalue(SubpacketEnum.ACCELERATION_Y.value) == 4
    assert main_window.data.lastvalue(SubpacketEnum.ACCELERATION_Z.value) == 5
    assert main_window.data.lastvalue(SubpacketEnum.ORIENTATION_1.value) == 6
    assert main_window.data.lastvalue(SubpacketEnum.ORIENTATION_2.value) == 7
    assert main_window.data.lastvalue(SubpacketEnum.ORIENTATION_3.value) == 8
    assert main_window.data.lastvalue(SubpacketEnum.LATITUDE.value) == 9
    assert main_window.data.lastvalue(SubpacketEnum.LONGITUDE.value) == 10
    assert main_window.data.lastvalue(SubpacketEnum.STATE.value) == 11

    num = wait_for_event(snapshot, LABLES_UPDATED_EVENT, 'main_window.main')
    assert num == 1
    assert float(main_window.AltitudeLabel.text()) == 2.0
    assert main_window.GPSLabel.text() == '9.0, 10.0'
    assert float(main_window.StateLabel.text()) == 11.0

def test_message_packet(qtbot, caplog):
    connection = DebugConnection(generate_radio_packets=False)
    main_window = MainApp(connection, co_pilot)

    packet = radio_packets.message(0, "test_message")

    snapshot = get_event_stats_snapshot()

    connection.send_to_rocket(packet)

    num = wait_for_event(snapshot, BUNDLE_ADDED_EVENT, 'main_window.rocket_data')

    assert num == 1
    assert main_window.data.lastvalue(SubpacketEnum.MESSAGE.value) == "test_message"
    assert "test_message" in caplog.text

def test_config_packet(qtbot):
    connection = DebugConnection(generate_radio_packets=False)
    main_window = MainApp(connection, co_pilot)

    packet = radio_packets.config(0, True, 2)

    snapshot = get_event_stats_snapshot()

    connection.send_to_rocket(packet)

    num = wait_for_event(snapshot, BUNDLE_ADDED_EVENT, 'main_window.rocket_data')

    assert num == 1
    assert main_window.data.lastvalue(IS_SIM) == True
    assert main_window.data.lastvalue(ROCKET_TYPE) == 2

def test_status_ping_packet(qtbot):
    connection = DebugConnection(generate_radio_packets=False)
    main_window = MainApp(connection, co_pilot)

    packet = radio_packets.status_ping(0, radio_packets.StatusType.CRITICAL_FAILURE, 0xFF, 0xFF, 0xFF, 0xFF)

    snapshot = get_event_stats_snapshot()

    connection.send_to_rocket(packet)

    num = wait_for_event(snapshot, BUNDLE_ADDED_EVENT, 'main_window.rocket_data')

    assert num == 1
    assert main_window.data.lastvalue(SubpacketEnum.STATUS_PING.value) == NONCRITICAL_FAILURE
    for sensor in SENSOR_TYPES:
        assert main_window.data.lastvalue(sensor) == 1
    for other in OTHER_STATUS_TYPES:
        assert main_window.data.lastvalue(other) == 1
