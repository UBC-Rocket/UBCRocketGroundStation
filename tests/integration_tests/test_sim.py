import pytest
from pytest import approx
from .integration_utils import test_app, valid_paramitrization, all_devices, all_profiles, only_flare, flush_packets
from connections.sim.sim_connection import FirmwareNotFound
from connections.sim.hw_sim import HWSim, SensorType
from main_window.competition.comp_app import CompApp
from main_window.data_entry_id import DataEntryIds
from main_window.device_manager import DeviceType
from main_window.packet_parser import (
    SINGLE_SENSOR_EVENT,
    CONFIG_EVENT,
)

from util.event_stats import get_event_stats_snapshot


@pytest.fixture(scope="function")
def sim_app(test_app, request) -> CompApp:
    profile = request.param
    try:
        connections = profile.construct_sim_connection()
    except FirmwareNotFound:
        pytest.skip("Firmware not found")
        return

    return test_app(profile, connections)



def get_hw_sim(sim_app, device_type: DeviceType) -> HWSim:
    connection_name = sim_app.device_manager.get_full_address(device_type).connection_name
    return sim_app.connections[connection_name]._hw_sim


def set_dummy_sensor_values(sim_app, device_type: DeviceType, sensor_type: SensorType, *vals):
    hw = get_hw_sim(sim_app, device_type)
    with hw.lock:
        hw._sensors[sensor_type].set_value(tuple(vals))


@pytest.mark.parametrize(
    "sim_app, device_type", valid_paramitrization(
        all_profiles(excluding=['WbProfile', 'CoPilotProfile']),
        only_flare(all_devices())),
    indirect=['sim_app'])
class TestFlare:
    def test_arming(self, qtbot, sim_app, device_type):
        flush_packets(sim_app, device_type)
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == 0

        sim_app.send_command(device_type.name + ".arm")
        flush_packets(sim_app, device_type)

        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == 1

        sim_app.send_command(device_type.name + ".disarm")
        flush_packets(sim_app, device_type)

        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == 0

    def test_config_hello(self, qtbot, sim_app, device_type):
        flush_packets(sim_app, device_type)
        # Should have already received at least one config packet from the startup hello
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.IS_SIM) == True
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.DEVICE_TYPE) == device_type

        snapshot = get_event_stats_snapshot()

        sim_app.send_command(device_type.name + ".config")
        flush_packets(sim_app, device_type)
        assert CONFIG_EVENT.wait(snapshot) == 1

        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.IS_SIM) == True
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.VERSION_ID) is not None
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.DEVICE_TYPE) == device_type

    def test_gps_read(self, qtbot, sim_app, device_type):
        test_vals = [
            (11, 12, 13),
            (21, 22, 23),
            (31, 32, 33),
        ]

        for vals in test_vals:
            set_dummy_sensor_values(sim_app, device_type, SensorType.GPS, *vals)
            flush_packets(sim_app, device_type)
            snapshot = get_event_stats_snapshot()
            sim_app.send_command(device_type.name + ".gpsalt")
            assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1

            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.LATITUDE) == vals[0]
            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.LONGITUDE) == vals[1]
            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.GPS_ALTITUDE) == vals[2]

    def test_baro_altitude(self, qtbot, sim_app, device_type):
        Pb = 101325
        Tb = 288.15
        Lb = -0.0065
        R = 8.3144598
        g0 = 9.80665
        M = 0.0289644
        altitude = lambda pres: Tb / Lb * ((Pb / pres) ** (R * Lb / (g0 * M)) - 1)

        hw = get_hw_sim(sim_app, device_type)

        # Set base/ground altitude
        ground_pres = hw.sensor_read(SensorType.BAROMETER)[0]
        set_dummy_sensor_values(sim_app, device_type, SensorType.BAROMETER, ground_pres, 25)
        flush_packets(sim_app, device_type)
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.CALCULATED_ALTITUDE) == 0

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
            set_dummy_sensor_values(sim_app, device_type, SensorType.BAROMETER, *vals)
            flush_packets(sim_app, device_type)

            snapshot = get_event_stats_snapshot()
            sim_app.send_command(device_type.name + ".baropres")
            sim_app.send_command(device_type.name + ".barotemp")
            assert SINGLE_SENSOR_EVENT.wait(snapshot, num_expected=2) == 2

            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.PRESSURE) == vals[0]
            assert sim_app.rocket_data.last_value_by_device(device_type,
                                                            DataEntryIds.BAROMETER_TEMPERATURE) == vals[1]
            assert sim_app.rocket_data.last_value_by_device(device_type,
                                                            DataEntryIds.CALCULATED_ALTITUDE) == approx(
                altitude(vals[0]) - altitude(ground_pres), 0.1)
            assert sim_app.rocket_data.last_value_by_device(device_type,
                                                            DataEntryIds.BAROMETER_TEMPERATURE) == vals[1]

    def test_accelerometer_read(self, qtbot, sim_app, device_type):
        test_vals = [
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        ]

        for vals in test_vals:
            set_dummy_sensor_values(sim_app, device_type, SensorType.ACCELEROMETER, *vals)
            flush_packets(sim_app, device_type)

            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.ACCELERATION_X) == vals[0]
            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.ACCELERATION_Y) == vals[1]
            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.ACCELERATION_Z) == vals[2]

    def test_imu_read(self, qtbot, sim_app, device_type):
        test_vals = [
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        ]

        for vals in test_vals:
            set_dummy_sensor_values(sim_app, device_type, SensorType.IMU, *vals)
            flush_packets(sim_app, device_type)

            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.ORIENTATION_1) == vals[
                0]  # TODO Problematic dependency on subpacket_ids
            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.ORIENTATION_2) == vals[1]
            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.ORIENTATION_3) == vals[2]

    def test_temperature_read(self, qtbot, sim_app, device_type):
        test_vals = [
            (0,),
            (10,),
            (20,),
        ]

        for vals in test_vals:
            set_dummy_sensor_values(sim_app, device_type, SensorType.TEMPERATURE, *vals)
            flush_packets(sim_app, device_type)  # Just to wait a few cycles for the FW to read from HW sim
            snapshot = get_event_stats_snapshot()
            sim_app.send_command(device_type.name + ".TEMP")
            assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1

            assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.TEMPERATURE) == vals[0]

    def test_time_update(self, qtbot, sim_app, device_type):
        hw = get_hw_sim(sim_app, device_type)

        flush_packets(sim_app, device_type)
        initial = sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.TIME)
        hw.time_update(1000)
        flush_packets(sim_app, device_type)
        final = sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.TIME)
        delta = final - initial
        assert delta >= 1000


@pytest.mark.parametrize("sim_app", valid_paramitrization(all_profiles(excluding=['WbProfile', 'CoPilotProfile'])),
                         indirect=True)
def test_clean_shutdown(qtbot, sim_app):
    assert sim_app.ReadThread.isRunning()
    assert sim_app.SendThread.isRunning()
    assert sim_app.MappingThread.isRunning()
    assert sim_app.MappingThread.map_process.is_alive()
    assert sim_app.rocket_data.autosave_thread.is_alive()
    for connection in sim_app.connections.values():
        assert connection.thread.is_alive()
        assert connection._xbee._rocket_rx_thread.is_alive()
        assert connection.rocket.poll() is None

    sim_app.shutdown()

    assert sim_app.ReadThread.isFinished()
    assert sim_app.SendThread.isFinished()
    assert sim_app.MappingThread.isFinished()
    assert not sim_app.rocket_data.autosave_thread.is_alive()
    for connection in sim_app.connections.values():
        assert not connection.thread.is_alive()
        assert not connection._xbee._rocket_rx_thread.is_alive()
        assert connection.rocket.poll() is not None

    with pytest.raises(ValueError):
        sim_app.MappingThread.map_process.is_alive()
