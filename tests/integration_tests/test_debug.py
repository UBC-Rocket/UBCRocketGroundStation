import pytest
from unittest.mock import MagicMock, ANY
from .integration_utils import test_app, valid_paramitrization, all_profiles
from connections.debug.debug_connection import DebugConnection, ARMED_EVENT, DISARMED_EVENT
from main_window.competition.comp_app import LABELS_UPDATED_EVENT
from profiles.rockets.bnb import BNBProfile
from connections.debug import radio_packets
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.data_entry_id import DataEntryIds, DataEntryValues
from main_window.device_manager import DeviceType, DEVICE_REGISTERED_EVENT
from main_window.send_thread import COMMAND_SENT_EVENT
from main_window.packet_parser import (
    VERSION_ID_LEN,
    SINGLE_SENSOR_EVENT,
    EVENT_EVENT,
    CONFIG_EVENT,
    STATE_EVENT,
    DEVICE_TYPE_TO_ID,
    SubpacketIds, STATE_IDS, EVENT_IDS)
from main_window.competition.comp_packet_parser import (
    SENSOR_TYPES,
    OTHER_STATUS_TYPES,
    BULK_SENSOR_EVENT,
)

from util.event_stats import get_event_stats_snapshot
from util.detail import REQUIRED_FLARE


@pytest.fixture(scope="function")
def single_connection_bnb(test_app):
    yield test_app(BNBProfile(), {
        'DEBUG_CONNECTION': DebugConnection('BNB_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_1_FLARE], generate_radio_packets=False)
    }, num_devices=1)


def test_arm_signal(qtbot, single_connection_bnb):
    app = single_connection_bnb
    snapshot = get_event_stats_snapshot()

    app.send_command("bnb_stage_1_flare.arm")

    assert ARMED_EVENT.wait(snapshot) == 1

    app.send_command("bnb_stage_1_flare.disarm")

    assert DISARMED_EVENT.wait(snapshot) == 1


def test_bulk_sensor_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    state_input = 0x09
    sensor_inputs = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, state_input)

    packet = radio_packets.bulk_sensor(*sensor_inputs)

    snapshot = get_event_stats_snapshot()

    with qtbot.waitSignal(
            app.ReadThread.sig_received
    ):  # Needed otherwise signals wont process because UI is in same thread
        connection.receive(packet)

    assert STATE_EVENT.wait(snapshot) == 1
    assert BULK_SENSOR_EVENT.wait(snapshot) == 1

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    def get_val(val):
        return app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, val)

    vals_to_get = (
        DataEntryIds.CALCULATED_ALTITUDE,
        DataEntryIds.ACCELERATION_X,
        DataEntryIds.ACCELERATION_Y,
        DataEntryIds.ACCELERATION_Z,
        DataEntryIds.ORIENTATION_1,
        DataEntryIds.ORIENTATION_2,
        DataEntryIds.ORIENTATION_3,
        DataEntryIds.LATITUDE,
        DataEntryIds.LONGITUDE,
    )
    last_values = tuple(map(get_val, vals_to_get))

    # Only check items in tuple vals_to_get
    assert sensor_inputs[1:-1] == last_values

    # Special check for state
    state_val = get_val(DataEntryIds.STATE)
    assert STATE_IDS[state_input] == state_val

    assert LABELS_UPDATED_EVENT.wait(snapshot) >= 1

    assert app.Stage1AltitudeLabel.text() == '2.00 m'
    assert app.Stage1GPSLabel.text() == '9.00000\xb0, 10.00000\xb0'
    assert app.Stage1StateLabel.text() == STATE_IDS[state_input].name


def test_single_sensor_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    vals = [
        (SubpacketIds.ACCELERATION_Y, 1),
        (SubpacketIds.ACCELERATION_X, 2),
        (SubpacketIds.ACCELERATION_Z, 3),
        (SubpacketIds.PRESSURE, 4),
        (SubpacketIds.BAROMETER_TEMPERATURE, 5),
        (SubpacketIds.TEMPERATURE, 6),
        (SubpacketIds.LATITUDE, 7),
        (SubpacketIds.LONGITUDE, 8),
        (SubpacketIds.GPS_ALTITUDE, 9),
        (SubpacketIds.CALCULATED_ALTITUDE, 10),
        (SubpacketIds.GROUND_ALTITUDE, 12),

        (SubpacketIds.ACCELERATION_Y, 13),
        (SubpacketIds.ACCELERATION_X, 14),
        (SubpacketIds.ACCELERATION_Z, 15),
        (SubpacketIds.PRESSURE, 16),
        (SubpacketIds.BAROMETER_TEMPERATURE, 17),
        (SubpacketIds.TEMPERATURE, 18),
        (SubpacketIds.LATITUDE, 19),
        (SubpacketIds.LONGITUDE, 20),
        (SubpacketIds.GPS_ALTITUDE, 21),
        (SubpacketIds.CALCULATED_ALTITUDE, 22),
        (SubpacketIds.GROUND_ALTITUDE, 24),
    ]

    for sensor_id, val in vals:
        data_entry_id = DataEntryIds[sensor_id.name]
        packet = radio_packets.single_sensor(0xFFFFFFFF, sensor_id, val)

        snapshot = get_event_stats_snapshot()

        connection.receive(packet)

        assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1
        assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                    DataEntryIds.TIME) == 0xFFFFFFFF
        assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, data_entry_id) == val


def test_event_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']
    event_to_test = 0x00
    packet = radio_packets.event(0xFFFFFFFF, event_to_test)
    snapshot = get_event_stats_snapshot()
    connection.receive(packet)

    assert EVENT_EVENT.wait(snapshot) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.EVENT) == EVENT_IDS[event_to_test]

def test_state_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']
    state_to_test = 0x00
    packet = radio_packets.state(0xFFFFFFFF, state_to_test)
    snapshot = get_event_stats_snapshot()
    connection.receive(packet)

    assert STATE_EVENT.wait(snapshot) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.STATE) == STATE_IDS[state_to_test]


def test_message_packet(qtbot, single_connection_bnb, caplog):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    packet = radio_packets.message(0xFFFFFFFF, "test_message")

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.MESSAGE) == "test_message"
    assert "test_message" in caplog.text


def test_config_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    version_id = REQUIRED_FLARE
    assert len(version_id) == VERSION_ID_LEN  # make sure test val is acceptable

    packet = radio_packets.config(0xFFFFFFFF, True, 0x00, version_id)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert CONFIG_EVENT.wait(snapshot) == 1
    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.IS_SIM) == True
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.DEVICE_TYPE) == DeviceType.BNB_STAGE_1_FLARE
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.VERSION_ID) == version_id


def test_status_ping_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    packet = radio_packets.status_ping(
        0xFFFFFFFF, radio_packets.StatusType.CRITICAL_FAILURE, 0xFF, 0xFF, 0xFF, 0xFF
    )

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert (
            app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.OVERALL_STATUS)
            == DataEntryValues.STATUS_CRITICAL_FAILURE
    )
    for sensor in SENSOR_TYPES:
        assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, sensor) == 1
    for other in OTHER_STATUS_TYPES:
        assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, other) == 1


def test_gps_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    gps_inputs = (0xFFFFFFFF, 1, 2, 3)

    packet = radio_packets.gps(*gps_inputs)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.LATITUDE) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.LONGITUDE) == 2
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.GPS_ALTITUDE) == 3


def test_orientation_packet(qtbot, single_connection_bnb):
    app = single_connection_bnb
    connection = app.connections['DEBUG_CONNECTION']

    orientation_inputs = (0xFFFFFFFF, 1, 2, 3, 4)

    packet = radio_packets.orientation(*orientation_inputs)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.TIME) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.ORIENTATION_1) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.ORIENTATION_2) == 2
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.ORIENTATION_3) == 3
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE,
                                                DataEntryIds.ORIENTATION_4) == 4


def test_multi_connection_receive(qtbot, test_app):
    con_a = DebugConnection('BNB_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_1_FLARE],
                            generate_radio_packets=False)
    con_b = DebugConnection('BNB_STAGE_2_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_2_FLARE],
                            generate_radio_packets=False)
    snapshot = get_event_stats_snapshot()
    app = test_app(BNBProfile(), {'DEBUG_CONNECTION_1': con_a, 'DEBUG_CONNECTION_2': con_b}, num_devices=2)

    con_a.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketIds.PRESSURE, 1))
    con_b.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketIds.PRESSURE, 2))

    # Fake some other device on same connection
    con_a.device_address = 'OTHER_ADDRESS'
    sample_version = '1234567890123456789012345678901234567890'
    con_a.receive(radio_packets.config(0xFFFFFFFF, True, DEVICE_TYPE_TO_ID[DeviceType.CO_PILOT_FLARE], sample_version))
    con_a.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketIds.PRESSURE, 3))

    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=3) == 3
    assert BUNDLE_ADDED_EVENT.wait(snapshot, num_expected=6) == 6

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, DataEntryIds.PRESSURE) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_2_FLARE, DataEntryIds.PRESSURE) == 2
    assert app.rocket_data.last_value_by_device(DeviceType.CO_PILOT_FLARE, DataEntryIds.PRESSURE) == 3


def test_multi_connection_commands(qtbot, test_app):
    con_a = DebugConnection('BNB_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_1_FLARE],
                            generate_radio_packets=False)
    con_b = DebugConnection('BNB_STAGE_2_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_2_FLARE],
                            generate_radio_packets=False)

    con_a.send = MagicMock()
    con_b.send = MagicMock()

    snapshot = get_event_stats_snapshot()
    app = test_app(BNBProfile(), {'DEBUG_CONNECTION_1': con_a, 'DEBUG_CONNECTION_2': con_b}, num_devices=2)

    # Fake some other device on same connection
    con_a.device_address = 'OTHER_ADDRESS'
    sample_version = '1234567890123456789012345678901234567890'
    con_a.receive(radio_packets.config(0xFFFFFFFF, True, DEVICE_TYPE_TO_ID[DeviceType.CO_PILOT_FLARE], sample_version))

    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=3) == 3

    # Send commands to each and assert called

    snapshot = get_event_stats_snapshot()
    app.send_command("bnb_stage_1_flare.arm")
    COMMAND_SENT_EVENT.wait(snapshot)
    con_a.send.assert_called_with('BNB_STAGE_1_ADDRESS', ANY)

    snapshot = get_event_stats_snapshot()
    app.send_command("bnb_stage_2_flare.arm")
    COMMAND_SENT_EVENT.wait(snapshot)
    con_b.send.assert_called_with('BNB_STAGE_2_ADDRESS', ANY)

    snapshot = get_event_stats_snapshot()
    app.send_command("co_pilot_flare.arm")
    COMMAND_SENT_EVENT.wait(snapshot)
    con_a.send.assert_called_with('OTHER_ADDRESS', ANY)


def test_register_after_data(qtbot, test_app):
    con = DebugConnection('BNB_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_1_FLARE],
                          generate_radio_packets=False)
    app = test_app(BNBProfile(), {'DEBUG_CONNECTION': con}, num_devices=1)
    snapshot = get_event_stats_snapshot()

    # Fake stage 2 on same connection
    con.device_address = 'BNB_STAGE_2_ADDRESS'
    con.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketIds.PRESSURE, 1))
    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    # Cause device to register
    con.receive(radio_packets.config(0xFFFFFFFF, True, DEVICE_TYPE_TO_ID[DeviceType.BNB_STAGE_2_FLARE], REQUIRED_FLARE))
    assert DEVICE_REGISTERED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.BNB_STAGE_2_FLARE, DataEntryIds.PRESSURE) == 1


@pytest.mark.parametrize("profile", valid_paramitrization(all_profiles(excluding='WbProfile')))
def test_clean_shutdown(qtbot, profile):
    app = profile.construct_app(profile.construct_debug_connection())

    assert app.ReadThread.isRunning()
    assert app.SendThread.isRunning()
    assert app.MappingThread.isRunning()
    assert app.MappingThread.map_process.is_alive()
    assert app.rocket_data.autosave_thread.is_alive()
    for connection in app.connections.values():
        assert connection.connectionThread.is_alive()

    app.shutdown()

    assert app.ReadThread.isFinished()
    assert app.SendThread.isFinished()
    assert app.MappingThread.isFinished()
    assert not app.rocket_data.autosave_thread.is_alive()
    for connection in app.connections.values():
        assert not connection.connectionThread.is_alive()

    with pytest.raises(ValueError):
        app.MappingThread.map_process.is_alive()
