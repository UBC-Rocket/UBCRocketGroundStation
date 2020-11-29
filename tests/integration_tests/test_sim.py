import pytest
import logging
from pytest import approx
from .integration_app import integration_app
from connections.sim.sim_connection import FirmwareNotFound
from connections.sim.hw_sim import SensorType, SENSOR_READ_EVENT
from main_window.competition.comp_app import CompApp
from profiles.rockets.tantalus import TantalusProfile
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.device_manager import DeviceType, DEVICE_REGISTERED_EVENT
from main_window.packet_parser import (
    IS_SIM,
    DEVICE_TYPE,
    SINGLE_SENSOR_EVENT,
    CONFIG_EVENT,
    VERSION_ID,
)
from main_window.competition.comp_packet_parser import BULK_SENSOR_EVENT

from util.event_stats import get_event_stats_snapshot


@pytest.fixture(scope="function")
def main_app(integration_app) -> CompApp:
    profile = TantalusProfile()
    try:
        connections = profile.construct_sim_connection()
    except FirmwareNotFound as ex:
        pytest.skip("Firmware not found")
        return
    
    yield integration_app(profile, connections)


def set_dummy_sensor_values(hw, sensor_type: SensorType, *vals):
    with hw.lock:
        hw._sensors[sensor_type].set_value(tuple(vals))


def wait_new_bundle():
    # Wait a few update cycles to flush any old packets out
    for i in range(5):
        snapshot = get_event_stats_snapshot()
        assert SENSOR_READ_EVENT.wait(snapshot) >= 1
        assert BULK_SENSOR_EVENT.wait(snapshot) >= 1
        assert BUNDLE_ADDED_EVENT.wait(snapshot) >= 1


def test_arming(qtbot, main_app):
    wait_new_bundle()
    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.STATE.value) == 0

    main_app.send_command("tantalus_stage_1.arm")
    wait_new_bundle()

    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.STATE.value) == 1

    main_app.send_command("tantalus_stage_1.disarm")
    wait_new_bundle()

    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.STATE.value) == 0

def test_config_hello(qtbot, main_app):
    wait_new_bundle()
    # Should have already received at least one config packet from the startup hello
    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, IS_SIM) == True
    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, DEVICE_TYPE) == DeviceType.TANTALUS_STAGE_1

    snapshot = get_event_stats_snapshot()
    main_app.send_command("tantalus_stage_1.config")
    wait_new_bundle()
    assert CONFIG_EVENT.wait(snapshot) == 1

    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, IS_SIM) == True
    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, VERSION_ID) is not None
    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, DEVICE_TYPE) == DeviceType.TANTALUS_STAGE_1


def test_gps_read(qtbot, main_app):
    connection = main_app.connections['TANTALUS_STAGE_1_CONNECTION']
    hw = connection._hw_sim

    test_vals = [
        (11, 12, 13),
        (21, 22, 23),
        (31, 32, 33),
    ]

    for vals in test_vals:
        set_dummy_sensor_values(hw, SensorType.GPS, *vals)
        wait_new_bundle()
        snapshot = get_event_stats_snapshot()
        main_app.send_command("tantalus_stage_1.gpsalt")
        assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1

        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.LATITUDE.value) == vals[0]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.LONGITUDE.value) == vals[1]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.GPS_ALTITUDE.value) == vals[2]


def test_baro_altitude(qtbot, main_app):
    Pb = 101325
    Tb = 288.15
    Lb = -0.0065
    R = 8.3144598
    g0 = 9.80665
    M = 0.0289644
    altitude = lambda pres: Tb / Lb * ((Pb / pres) ** (R * Lb / (g0 * M)) - 1)

    connection = main_app.connections['TANTALUS_STAGE_1_CONNECTION']
    hw = connection._hw_sim

    # Set base/ground altitude
    ground_pres = hw.sensor_read(SensorType.BAROMETER)[0]
    set_dummy_sensor_values(hw, SensorType.BAROMETER, ground_pres, 25)
    wait_new_bundle()
    assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.CALCULATED_ALTITUDE.value) == 0

    # Note: Kind of a hack because ground altitude is only solidified once rocket launches. Here we are abusing the
    # fact that we dont update the ground altitude if the pressure change is too large. This allows us to run these
    # tests in the standby state

    test_vals = [
        (1500, 25),
        (1000, 25),
        (500, 25),
        (250, 32),
    ]

    for vals in test_vals:
        set_dummy_sensor_values(hw, SensorType.BAROMETER, *vals)
        wait_new_bundle()

        snapshot = get_event_stats_snapshot()
        main_app.send_command("tantalus_stage_1.baropres")
        main_app.send_command("tantalus_stage_1.barotemp")
        assert SINGLE_SENSOR_EVENT.wait(snapshot, num_expected=2) == 2

        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.PRESSURE.value) == vals[0]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.BAROMETER_TEMPERATURE.value) == vals[1]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.CALCULATED_ALTITUDE.value) == approx(
            altitude(vals[0]) - altitude(ground_pres), 0.1)
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.BAROMETER_TEMPERATURE.value) == vals[1]


def test_accelerometer_read(qtbot, main_app):
    connection = main_app.connections['TANTALUS_STAGE_1_CONNECTION']
    hw = connection._hw_sim

    test_vals = [
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
    ]

    for vals in test_vals:
        set_dummy_sensor_values(hw, SensorType.ACCELEROMETER, *vals)
        wait_new_bundle()

        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.ACCELERATION_X.value) == vals[0]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.ACCELERATION_Y.value) == vals[1]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.ACCELERATION_Z.value) == vals[2]


def test_imu_read(qtbot, main_app):
    connection = main_app.connections['TANTALUS_STAGE_1_CONNECTION']
    hw = connection._hw_sim

    test_vals = [
        (1, 0, 0, 0),
        (0, 1, 0, 0),
        (0, 0, 1, 0),
        (0, 0, 0, 1),
    ]

    for vals in test_vals:
        set_dummy_sensor_values(hw, SensorType.IMU, *vals)
        wait_new_bundle()

        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.ORIENTATION_1.value) == vals[0] # TODO Problematic dependency on subpacket_ids
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.ORIENTATION_2.value) == vals[1]
        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.ORIENTATION_3.value) == vals[2]


def test_temperature_read(qtbot, main_app):
    connection = main_app.connections['TANTALUS_STAGE_1_CONNECTION']
    hw = connection._hw_sim

    test_vals = [
        (0,),
        (10,),
        (20,),
    ]

    for vals in test_vals:
        set_dummy_sensor_values(hw, SensorType.TEMPERATURE, *vals)
        wait_new_bundle()  # Just to wait a few cycles for the FW to read from HW sim
        snapshot = get_event_stats_snapshot()
        main_app.send_command("tantalus_stage_1.TEMP")
        assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1

        assert main_app.rocket_data.last_value_by_device(DeviceType.TANTALUS_STAGE_1, SubpacketEnum.TEMPERATURE.value) == vals[0]


def test_clean_shutdown(qtbot, main_app):
    assert main_app.ReadThread.isRunning()
    assert main_app.SendThread.isRunning()
    assert main_app.MappingThread.isRunning()
    assert main_app.MappingThread.map_process.is_alive()
    assert main_app.rocket_data.autosaveThread.is_alive()
    for connection in main_app.connections.values():
        assert connection.thread.is_alive()
        assert connection._xbee._rocket_rx_thread.is_alive()
        assert connection.rocket.poll() is None

    main_app.shutdown()

    assert main_app.ReadThread.isFinished()
    assert main_app.SendThread.isFinished()
    assert main_app.MappingThread.isFinished()
    assert not main_app.rocket_data.autosaveThread.is_alive()
    for connection in main_app.connections.values():
        assert not connection.thread.is_alive()
        assert not connection._xbee._rocket_rx_thread.is_alive()
        assert connection.rocket.poll() is not None

    with pytest.raises(ValueError):
        main_app.MappingThread.map_process.is_alive()