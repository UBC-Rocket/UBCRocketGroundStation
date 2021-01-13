import pytest
from unittest.mock import MagicMock, ANY
from .integration_utils import test_app, valid_paramitrization, all_profiles
from connections.debug.debug_connection import DebugConnection, ARMED_EVENT, DISARMED_EVENT
from main_window.competition.comp_app import LABLES_UPDATED_EVENT
from profiles.rockets.tantalus import TantalusProfile
from connections.debug import radio_packets
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.device_manager import DeviceType, DEVICE_REGISTERED_EVENT
from main_window.send_thread import COMMAND_SENT_EVENT
from main_window.packet_parser import (
    IS_SIM,
    DEVICE_TYPE,
    VERSION_ID,
    VERSION_ID_LEN,
    SINGLE_SENSOR_EVENT,
    CONFIG_EVENT,
    DEVICE_TYPE_TO_ID
)
from main_window.competition.comp_packet_parser import (
    CRITICAL_FAILURE,
    SENSOR_TYPES,
    OTHER_STATUS_TYPES,
    BULK_SENSOR_EVENT,
)

from util.event_stats import get_event_stats_snapshot
from util.detail import REQUIRED_FLARE


@pytest.fixture(scope="function")
def single_connection_tantalus(test_app):
    yield test_app(TantalusProfile(), {
        'DEBUG_CONNECTION': DebugConnection('TANTALUS_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE], generate_radio_packets=False)
    }, num_devices=1)


def test_arm_signal(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    snapshot = get_event_stats_snapshot()

    app.send_command("tantalus_stage_1_flare.arm")

    assert ARMED_EVENT.wait(snapshot) == 1

    app.send_command("tantalus_stage_1_flare.disarm")

    assert DISARMED_EVENT.wait(snapshot) == 1


def test_bulk_sensor_packet(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

    sensor_inputs = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

    packet = radio_packets.bulk_sensor(*sensor_inputs)

    snapshot = get_event_stats_snapshot()

    with qtbot.waitSignal(
            app.ReadThread.sig_received
    ):  # Needed otherwise signals wont process because UI is in same thread
        connection.receive(packet)

    assert BULK_SENSOR_EVENT.wait(snapshot) == 1

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    def get_val(val):
        return app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, val.value)

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

    assert LABLES_UPDATED_EVENT.wait(snapshot) >= 1

    assert float(app.AltitudeLabel.text()) == 2.0
    assert app.GPSLabel.text() == "9.0, 10.0"
    assert float(app.StateLabel.text()) == 11.0


def test_single_sensor_packet(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

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
        packet = radio_packets.single_sensor(0xFFFFFFFF, sensor_id.value, val)

        snapshot = get_event_stats_snapshot()

        connection.receive(packet)

        assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1

        assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                    SubpacketEnum.TIME.value) == 0xFFFFFFFF
        assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, sensor_id.value) == val


def test_message_packet(qtbot, single_connection_tantalus, caplog):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

    packet = radio_packets.message(0xFFFFFFFF, "test_message")

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.TIME.value) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.MESSAGE.value) == "test_message"
    assert "test_message" in caplog.text


def test_config_packet(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

    version_id = REQUIRED_FLARE
    assert len(version_id) == VERSION_ID_LEN  # make sure test val is acceptable

    packet = radio_packets.config(0xFFFFFFFF, True, 0x00, version_id)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert CONFIG_EVENT.wait(snapshot) == 1
    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.TIME.value) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, IS_SIM) == True
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                DEVICE_TYPE) == DeviceType.TANTALUS_STAGE_1_FLARE
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, VERSION_ID) == version_id


def test_status_ping_packet(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

    packet = radio_packets.status_ping(
        0xFFFFFFFF, radio_packets.StatusType.CRITICAL_FAILURE, 0xFF, 0xFF, 0xFF, 0xFF
    )

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.TIME.value) == 0xFFFFFFFF
    assert (
            app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, SubpacketEnum.STATUS_PING.value)
            == CRITICAL_FAILURE
    )
    for sensor in SENSOR_TYPES:
        assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, sensor) == 1
    for other in OTHER_STATUS_TYPES:
        assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, other) == 1


def test_gps_packet(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

    gps_inputs = (0xFFFFFFFF, 1, 2, 3)

    packet = radio_packets.gps(*gps_inputs)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.TIME.value) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, SubpacketEnum.LATITUDE.value) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, SubpacketEnum.LONGITUDE.value) == 2
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, SubpacketEnum.GPS_ALTITUDE.value) == 3


def test_orientation_packet(qtbot, single_connection_tantalus):
    app = single_connection_tantalus
    connection = app.connections['DEBUG_CONNECTION']

    orientation_inputs = (0xFFFFFFFF, 1, 2, 3, 4)

    packet = radio_packets.orientation(*orientation_inputs)

    snapshot = get_event_stats_snapshot()

    connection.receive(packet)

    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.TIME.value) == 0xFFFFFFFF
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.ORIENTATION_1.value) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.ORIENTATION_2.value) == 2
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.ORIENTATION_3.value) == 3
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE,
                                                SubpacketEnum.ORIENTATION_4.value) == 4


def test_multi_connection_receive(qtbot, test_app):
    con_a = DebugConnection('TANTALUS_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE],
                            generate_radio_packets=False)
    con_b = DebugConnection('TANTALUS_STAGE_2_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_2_FLARE],
                            generate_radio_packets=False)
    snapshot = get_event_stats_snapshot()
    app = test_app(TantalusProfile(), {'DEBUG_CONNECTION_1': con_a, 'DEBUG_CONNECTION_2': con_b}, num_devices=2)

    con_a.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketEnum.PRESSURE.value, 1))
    con_b.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketEnum.PRESSURE.value, 2))

    # Fake some other device on same connection
    con_a.device_address = 'OTHER_ADDRESS'
    con_a.receive(radio_packets.config(0xFFFFFFFF, True, DEVICE_TYPE_TO_ID[DeviceType.CO_PILOT_FLARE], 'version'))
    con_a.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketEnum.PRESSURE.value, 3))

    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=3) == 3
    assert BUNDLE_ADDED_EVENT.wait(snapshot, num_expected=6) == 6

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1_FLARE, SubpacketEnum.PRESSURE.value) == 1
    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_2_FLARE, SubpacketEnum.PRESSURE.value) == 2
    assert app.rocket_data.last_value_by_device(DeviceType.CO_PILOT_FLARE, SubpacketEnum.PRESSURE.value) == 3


def test_multi_connection_commands(qtbot, test_app):
    con_a = DebugConnection('TANTALUS_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE],
                            generate_radio_packets=False)
    con_b = DebugConnection('TANTALUS_STAGE_2_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_2_FLARE],
                            generate_radio_packets=False)

    con_a.send = MagicMock()
    con_b.send = MagicMock()

    snapshot = get_event_stats_snapshot()
    app = test_app(TantalusProfile(), {'DEBUG_CONNECTION_1': con_a, 'DEBUG_CONNECTION_2': con_b}, num_devices=2)

    # Fake some other device on same connection
    con_a.device_address = 'OTHER_ADDRESS'
    con_a.receive(radio_packets.config(0xFFFFFFFF, True, DEVICE_TYPE_TO_ID[DeviceType.CO_PILOT_FLARE], 'version'))

    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=3) == 3

    # Send commands to each and assert called

    snapshot = get_event_stats_snapshot()
    app.send_command("tantalus_stage_1_flare.arm")
    COMMAND_SENT_EVENT.wait(snapshot)
    con_a.send.assert_called_with('TANTALUS_STAGE_1_ADDRESS', ANY)

    snapshot = get_event_stats_snapshot()
    app.send_command("tantalus_stage_2_flare.arm")
    COMMAND_SENT_EVENT.wait(snapshot)
    con_b.send.assert_called_with('TANTALUS_STAGE_2_ADDRESS', ANY)

    snapshot = get_event_stats_snapshot()
    app.send_command("co_pilot_flare.arm")
    COMMAND_SENT_EVENT.wait(snapshot)
    con_a.send.assert_called_with('OTHER_ADDRESS', ANY)


def test_register_after_data(qtbot, test_app):
    con = DebugConnection('TANTALUS_STAGE_1_ADDRESS', DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_1_FLARE],
                          generate_radio_packets=False)
    app = test_app(TantalusProfile(), {'DEBUG_CONNECTION': con}, num_devices=1)
    snapshot = get_event_stats_snapshot()

    # Fake stage 2 on same connection
    con.device_address = 'TANTALUS_STAGE_2_ADDRESS'
    con.receive(radio_packets.single_sensor(0xFFFFFFFF, SubpacketEnum.PRESSURE.value, 1))
    assert BUNDLE_ADDED_EVENT.wait(snapshot) == 1

    # Cause device to register
    con.receive(radio_packets.config(0xFFFFFFFF, True, DEVICE_TYPE_TO_ID[DeviceType.TANTALUS_STAGE_2_FLARE], REQUIRED_FLARE))
    assert DEVICE_REGISTERED_EVENT.wait(snapshot) == 1

    assert app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_2_FLARE, SubpacketEnum.PRESSURE.value) == 1


@pytest.mark.parametrize("profile", valid_paramitrization(all_profiles(excluding='WbProfile')))
def test_clean_shutdown(qtbot, profile):
    app = profile.construct_app(profile.construct_debug_connection())

    assert app.ReadThread.isRunning()
    assert app.SendThread.isRunning()
    assert app.MappingThread.isRunning()
    assert app.MappingThread.map_process.is_alive()
    assert app.rocket_data.autosaveThread.is_alive()
    for connection in app.connections.values():
        assert connection.connectionThread.is_alive()

    app.shutdown()

    assert app.ReadThread.isFinished()
    assert app.SendThread.isFinished()
    assert app.MappingThread.isFinished()
    assert not app.rocket_data.autosaveThread.is_alive()
    for connection in app.connections.values():
        assert not connection.connectionThread.is_alive()

    with pytest.raises(ValueError):
        app.MappingThread.map_process.is_alive()
