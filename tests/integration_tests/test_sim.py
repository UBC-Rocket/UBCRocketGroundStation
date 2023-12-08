import time
import pytest
import numpy as np
from pytest import approx

from profiles.rocket_profile import RocketProfile
from profiles.rockets.silvertip import SilvertipProfile
from .integration_utils import test_app, valid_paramitrization, all_devices, all_profiles, only_flare, flush_packets
from connections.sim.sim_connection import FirmwareNotFound
from connections.sim.hw.hw_sim import HWSim, PinModes
from connections.sim.hw.sensors.sensor import SensorType
from connections.sim.hw.sensors.dummy_sensor import DummySensor
from connections.sim.hw.sensors.voltage_sensor_sim import VoltageSensor
from connections.sim.hw.rocket_sim import FlightEvent, FlightDataType
from main_window.competition.comp_app import CompApp
from main_window.data_entry_id import DataEntryIds, DataEntryValues
from main_window.device_manager import DeviceType
from main_window.packet_parser import (
    SINGLE_SENSOR_EVENT,
    CONFIG_EVENT,
    STATE_IDS,
)

from util.event_stats import get_event_stats_snapshot

S_TO_MS = int(1e3)

@pytest.fixture(scope="function")
def sim_app(test_app, request) -> CompApp:
    profile = request.param
    try:
        connections = profile.construct_sim_connection()
    except FirmwareNotFound:
        pytest.skip("Firmware not found")
        return

    return test_app(profile, connections)

def get_connection_name(sim_app, device_type: DeviceType):
    return sim_app.device_manager.get_full_address(device_type).connection_name

def get_hw_sim(sim_app, device_type: DeviceType) -> HWSim:
    connection_name = get_connection_name(sim_app, device_type)
    return sim_app.connections[connection_name]._hw_sim


def get_profile(sim_app) -> RocketProfile:
    return sim_app.rocket_profile


def set_dummy_sensor_values(sim_app, device_type: DeviceType, sensor_type: SensorType, *vals):
    hw = get_hw_sim(sim_app, device_type)
    hw.replace_sensor(DummySensor(sensor_type, tuple(vals)))


@pytest.mark.parametrize(
    "sim_app, device_type", valid_paramitrization(
        all_profiles(excluding=['WbProfile', 'CoPilotProfile', 'HollyburnProfile']),
        only_flare(all_devices(excluding=[]))),
    indirect=['sim_app'])
class TestFlare:
    def test_arming(self, qtbot, sim_app, device_type):
        flush_packets(sim_app, device_type)
        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == DataEntryValues.STATE_STANDBY

        sim_app.send_command(device_type.name + ".arm")
        flush_packets(sim_app, device_type)

        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == DataEntryValues.STATE_ARMED

        sim_app.send_command(device_type.name + ".disarm")
        flush_packets(sim_app, device_type)

        assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == DataEntryValues.STATE_STANDBY

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

    def test_config_change_gs_address(self, qtbot, sim_app, device_type):
        flush_packets(sim_app, device_type)

        snapshot = get_event_stats_snapshot()

        sim_app.send_command(device_type.name + ".config")
        flush_packets(sim_app, device_type)

        assert CONFIG_EVENT.wait(snapshot) == 1

        for connection in sim_app.connections.values():
            connection._xbee.gs_address = b'\x00\x13\xa2\x00Ag\x8f\xc1'

        sim_app.send_command(device_type.name + ".config")
        flush_packets(sim_app, device_type)

        assert CONFIG_EVENT.wait(snapshot, num_expected=2) == 2

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

    def test_pin_mode(self, qtbot, sim_app, device_type):
        hw = get_hw_sim(sim_app, device_type)

        # Pin modes get flipped in _handleDigitalPinWrite & _handleAnalogRead?
        assert hw.get_pin_mode(31) == PinModes.INPUT
        assert hw.get_pin_mode(15) == PinModes.INPUT
        assert hw.get_pin_mode(20) == PinModes.INPUT
        assert hw.get_pin_mode(193) == PinModes.OUTPUT
        assert hw.get_pin_mode(200) == PinModes.OUTPUT

    # No voltage sensor in 2022/23
    # def test_voltage_reading(self, qtbot, sim_app, device_type):
    #     flush_packets(sim_app, device_type)
    #
    #     snapshot = get_event_stats_snapshot()
    #     sim_app.send_command(device_type.name + ".VOLT")
    #     assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1
    #
    #     last_battery_voltage = sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.VOLTAGE)
    #     assert(round(last_battery_voltage, 1) == VoltageSensor.NOMINAL_BATTERY_VOLTAGE)
    #     assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.EVENT) is None
    #
    #     # The ADC level of 863 gets converted to 10.9V in battery.cpp in FLARE 21899292dc39015570f795ef9e607081aab57e3e
    #     updated_voltage_sensor = VoltageSensor(dummy_adc_level=863)
    #     hw = get_hw_sim(sim_app, device_type)
    #     hw.replace_sensor(updated_voltage_sensor)
    #
    #     flush_packets(sim_app, device_type)
    #
    #     snapshot = get_event_stats_snapshot()
    #     sim_app.send_command(device_type.name + ".VOLT")
    #     assert SINGLE_SENSOR_EVENT.wait(snapshot) == 1
    #
    #     last_battery_voltage = sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.VOLTAGE)
    #     assert(round(last_battery_voltage, 1) == 10.9)
    #     assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.EVENT) \
    #            == DataEntryValues.EVENT_LOW_VOLTAGE

    def test_baro_altitude(self, qtbot, sim_app, device_type):
        Pb = 101325
        Tb = 288.15
        Lb = -0.0065
        R = 8.3144598
        g0 = 9.80665
        M = 0.0289644
        altitude = lambda pres: Tb / Lb * ((Pb / pres) ** (R * Lb / (g0 * M)) - 1)

        # Set base/ground altitude
        initial_pres = 1000
        set_dummy_sensor_values(sim_app, device_type, SensorType.BAROMETER, initial_pres, 25)
        flush_packets(sim_app, device_type)
        initial_altitude = sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.CALCULATED_ALTITUDE)

        # Disable ignitors to prevent sim from launching
        # TODO: This is not clean, fix this hack
        hw = get_hw_sim(sim_app, device_type)
        for ign in hw._ignitors.values():
            ign.action_fn = None

        # Note: Kind of a hack because ground altitude is only solidified once rocket launches. Here we are abusing the
        # fact that we dont update the ground altitude if the pressure change is too large. This allows us to run these
        # tests in the standby state

        test_vals = [
            (150000, 25),
            (100000, 25),
            (50000, 25),
            (25000, 32),
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
                                                            DataEntryIds.CALCULATED_ALTITUDE) - initial_altitude == \
                                                                approx(altitude(vals[0]) - altitude(initial_pres), abs=0.01)
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
            (1, 0, 0, 0, 0, 0, 0),
            (0, 1, 0, 0, 0, 0, 0),
            (0, 0, 1, 0, 0, 0, 0),
            (0, 0, 0, 1, 0, 0, 0),
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

    def test_command_response_reliability(self, qtbot, sim_app, device_type):
        CYCLES = 100

        recv = 0

        for i in range(CYCLES):
            snapshot = get_event_stats_snapshot()
            sim_app.send_command(device_type.name + ".baropres")
            assert SINGLE_SENSOR_EVENT.wait(snapshot, num_expected=1) == 1


@pytest.mark.parametrize(
    "sim_app, device_type", valid_paramitrization(
        [SilvertipProfile()],
        only_flare(all_devices(excluding=[]))),
    indirect=['sim_app'])
def test_full_flight(qtbot, sim_app, device_type):
    hw = get_hw_sim(sim_app, device_type)

    flush_packets(sim_app, device_type)
    assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == DataEntryValues.STATE_STANDBY

    sim_app.send_command(device_type.name + ".arm")
    flush_packets(sim_app, device_type)

    assert sim_app.rocket_data.last_value_by_device(device_type, DataEntryIds.STATE) == DataEntryValues.STATE_ARMED

    hw.launch()

    # Run simulation until complete
    stuck_count = 0
    last_time = None
    while True:
        time.sleep(1)
        with hw:
            if FlightEvent.GROUND_HIT in hw._rocket_sim.get_flight_events():
                break

            print(
                f"FLIGHT RUNNING: t = {hw._rocket_sim.get_time()}, alt = {hw._rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE)}")

            if hw._rocket_sim.get_time() != last_time or last_time is None:
                stuck_count = 0
            else:
                stuck_count += 1
                if stuck_count >= 5:
                    assert False  # Flight sim stuck

            last_time = hw._rocket_sim.get_time()

    profile = get_profile(sim_app)

    # Define helper function
    def assert_flight_point(name, flight_point, deployment_time, sim_event, initial_state, final_state):
        times, alts =  hw._rocket_sim.get_time_series(FlightDataType.TYPE_ALTITUDE)
        deployment_altitude = np.interp(deployment_time, times, alts)

        # Print some stats
        deploy_id = f"STATS_{profile.rocket_name.replace(' ', '_').upper()}_{name}"
        print(f"{deploy_id}_TIME = {deployment_time}")
        print(f"{deploy_id}_ALTITUDE = {deployment_altitude}")

        # Assert deployment is at expected time and altitude
        assert abs(deployment_time - flight_point.time) < flight_point.time_tolerance
        assert abs(deployment_altitude - flight_point.altitude) < flight_point.altitude_tolerance

        # Assert that received igniter fired event at expected time
        (times, events) = sim_app.rocket_data.time_series_by_device(device_type, DataEntryIds.EVENT)
        fired = False
        for i in range(len(times)):
            if events[i] is DataEntryValues.EVENT_IGNITOR_FIRED and \
                    abs(times[i] / S_TO_MS - hw._rocket_sim.get_launch_time() - flight_point.time) < flight_point.time_tolerance:
                fired = True
                break
        assert fired

        # Assert that simulation event happened at expected time
        sim_event_times = hw._rocket_sim.get_flight_events()[sim_event]
        found_event = False
        for t in sim_event_times:
            if abs(t - flight_point.time) < flight_point.time_tolerance:
                found_event = True
                break
        assert found_event

        # Assert states transition at expected time
        (times, states) = sim_app.rocket_data.time_series_by_device(device_type, DataEntryIds.STATE)
        transitioned = False
        for i in range(len(times)):
            if flight_point.time - flight_point.time_tolerance < times[i] / S_TO_MS - hw._rocket_sim.get_launch_time() < flight_point.time + flight_point.time_tolerance:
                if states[i] == initial_state and states[i+1] == final_state:
                    transitioned = True
                    break
        assert transitioned

    # Start asserting based on simulation results
    with hw:
        assert_flight_point('DROGUE_DEPLOY',
                            profile.expected_apogee_point,
                            hw._rocket_sim.get_drogue_deployment_time(),
                            FlightEvent.APOGEE,
                            DataEntryValues.STATE_ASCENT_TO_APOGEE,
                            DataEntryValues.STATE_PRESSURE_DELAY)

        assert_flight_point('MAIN_DEPLOY',
                            profile.expected_main_deploy_point,
                            hw._rocket_sim.get_main_deployment_time(),
                            FlightEvent.RECOVERY_DEVICE_DEPLOYMENT,
                            DataEntryValues.STATE_DROGUE_DESCENT,
                            DataEntryValues.STATE_MAIN_DESCENT)


@pytest.mark.parametrize("sim_app", valid_paramitrization(all_profiles(excluding=['WbProfile', 'CoPilotProfile', 'HollyburnProfile'])),
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
