import pytest
import logging
from connections.debug.debug_connection import DebugConnection, ARMED_EVENT, DISARMED_EVENT
from main_window.competition.comp_app import LABLES_UPDATED_EVENT
from profiles.rockets.co_pilot import CoPilotProfile
from connections.debug import radio_packets
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.packet_parser import (
    IS_SIM,
    ROCKET_TYPE,
    VERSION_ID,
    VERSION_ID_LEN,
    SINGLE_SENSOR_EVENT,
    CONFIG_EVENT,
    DeviceType,
)
from main_window.competition.comp_packet_parser import (
    NONCRITICAL_FAILURE,
    SENSOR_TYPES,
    OTHER_STATUS_TYPES,
    BULK_SENSOR_EVENT,
)

from util.event_stats import get_event_stats_snapshot

@pytest.fixture(scope="function")
def main_app(caplog):
    connection = DebugConnection(generate_radio_packets=False)
    app = CoPilotProfile().construct_app(connection)
    yield app  # Provides app, following code is run on cleanup
    app.shutdown()

    # Fail test if error message in logs since we catch most exceptions in app
    for when in ("setup", "call"):
        messages = [x.message for x in caplog.get_records(when) if x.levelno == logging.ERROR]
        if messages:
            pytest.fail(f"Errors reported in logs: {messages}")

def test_arm_signal(qtbot, main_app):
    snapshot = get_event_stats_snapshot()

    main_app.send_command("arm")

    assert ARMED_EVENT.wait(snapshot) == 1

    main_app.send_command("disarm")

    assert DISARMED_EVENT.wait(snapshot) == 1



def test_bulk_sensor_packet(qtbot, main_app):
    connection = main_app.connection

    sensor_inputs = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

    packet = radio_packets.bulk_sensor(*sensor_inputs)

    snapshot = get_event_stats_snapshot()

    with qtbot.waitSignal(
            main_app.ReadThread.sig_received
    ):  # Needed otherwise signals wont process because UI is in same thread
        connection.receive(packet)

    assert BULK_SENSOR_EVENT.wait(snapshot) == 1

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

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

    assert LABLES_UPDATED_EVENT.wait(snapshot) == 1

    assert float(main_app.AltitudeLabel.text()) == 2.0
    assert main_app.GPSLabel.text() == "9.0, 10.0"
    assert float(main_app.StateLabel.text()) == 11.0

def test_single_sensor_packet(qtbot, main_app):
    connection = main_app.connection

    vals = [
        (SubpacketEnum.ACCELERATION_Y, 1),
        (SubpacketEnum.ACCELERATION_X, 2),
        (SubpacketEnum.ACCELERATION_Z, 3),
        (SubpacketEnum.PRESSURE, 4),
        (SubpacketEnum.BAROMETER_TEMPERATURE, 5),
        (SubpacketEnum.TEMPERATURE, 6),
        (SubpacketEnum.LATITUDE, 7),
        (SubpacketEnum.LONGITUDE, 8),
        (SubpacketEnum.GPS_ALTITUDE, 9),
        (SubpacketEnum.CALCULATED_ALTITUDE, 10),
        (SubpacketEnum.GROUND_ALTITUDE, 12),

        (SubpacketEnum.ACCELERATION_Y, 13),
        (SubpacketEnum.ACCELERATION_X, 14),
        (SubpacketEnum.ACCELERATION_Z, 15),
        (SubpacketEnum.PRESSURE, 16),
        (SubpacketEnum.BAROMETER_TEMPERATURE, 17),
        (SubpacketEnum.TEMPERATURE, 18),
        (SubpacketEnum.LATITUDE, 19),
        (SubpacketEnum.LONGITUDE, 20),
        (SubpacketEnum.GPS_ALTITUDE, 21),
        (SubpacketEnum.CALCULATED_ALTITUDE, 22),
        (SubpacketEnum.GROUND_ALTITUDE, 24),
    ]

    for sensor_id, val in vals:
        packet = radio_packets.single_sensor(0, sensor_id.value, val)

        snapshot = get_event_stats_snapshot()

        connection.receive(packet)

        assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1

        assert main_app.rocket_data.lastvalue(sensor_id.value) == val

def test_message_packet(qtbot, main_app, caplog):
    connection = main_app.connection

    packet = radio_packets.message(0, "test_message")

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert main_app.rocket_data.lastvalue(SubpacketEnum.MESSAGE.value) == "test_message"
    assert "test_message" in caplog.text


def test_config_packet(qtbot, main_app):
    connection = main_app.connection

    version_id = 'e43f15ba448653b34c043cf90593346e7ca4f9c7'
    assert len(version_id) == VERSION_ID_LEN # make sure test val is acceptable

    packet = radio_packets.config(0, True, 2, version_id)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert CONFIG_EVENT.wait(snapshot) == 1
    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert main_app.rocket_data.lastvalue(IS_SIM) == True
    assert main_app.rocket_data.lastvalue(ROCKET_TYPE) == DeviceType.CO_PILOT
    assert main_app.rocket_data.lastvalue(VERSION_ID) == version_id


def test_status_ping_packet(qtbot, main_app):
    connection = main_app.connection

    packet = radio_packets.status_ping(
        0, radio_packets.StatusType.CRITICAL_FAILURE, 0xFF, 0xFF, 0xFF, 0xFF
    )

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert (
            main_app.rocket_data.lastvalue(SubpacketEnum.STATUS_PING.value)
            == NONCRITICAL_FAILURE
    )
    for sensor in SENSOR_TYPES:
        assert main_app.rocket_data.lastvalue(sensor) == 1
    for other in OTHER_STATUS_TYPES:
        assert main_app.rocket_data.lastvalue(other) == 1


def test_gps_packet(qtbot, main_app):
    connection = main_app.connection

    gps_inputs = (0, 1, 2, 3)

    packet = radio_packets.gps(*gps_inputs)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert main_app.rocket_data.lastvalue(SubpacketEnum.TIME.value) == 0
    assert main_app.rocket_data.lastvalue(SubpacketEnum.LATITUDE.value) == 1
    assert main_app.rocket_data.lastvalue(SubpacketEnum.LONGITUDE.value) == 2
    assert main_app.rocket_data.lastvalue(SubpacketEnum.GPS_ALTITUDE.value) == 3


def test_orientation_packet(qtbot, main_app):
    connection = main_app.connection

    orientation_inputs = (0, 1, 2, 3, 4)

    packet = radio_packets.orientation(*orientation_inputs)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert main_app.rocket_data.lastvalue(SubpacketEnum.TIME.value) == 0
    assert main_app.rocket_data.lastvalue(SubpacketEnum.ORIENTATION_1.value) == 1
    assert main_app.rocket_data.lastvalue(SubpacketEnum.ORIENTATION_2.value) == 2
    assert main_app.rocket_data.lastvalue(SubpacketEnum.ORIENTATION_3.value) == 3
    assert main_app.rocket_data.lastvalue(SubpacketEnum.ORIENTATION_4.value) == 4


def test_clean_shutdown(qtbot):
    connection = DebugConnection(generate_radio_packets=True)
    main_app = CoPilotProfile().construct_app(connection)

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
