import pytest
from connections.sim.sim_connection_factory import SimConnectionFactory, FirmwareNotFound
from connections.sim.sim_connection import SimConnection
from connections.sim.hw_sim import SensorType, SENSOR_READ_EVENT
from main_window.main import MainApp
from profiles.rockets.tantalus import TantalusProfile
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.radio_controller import BULK_SENSOR_EVENT

from util.event_stats import get_event_stats_snapshot


def try_get_connection(rocket_profile) -> SimConnection:
    try:
        return SimConnectionFactory().construct(rocket=rocket_profile)
    except FirmwareNotFound as ex:
        pytest.skip("Firmware not found")

def test_gps_read(qtbot):
    connection = try_get_connection(TantalusProfile())
    main_window = MainApp(connection, TantalusProfile())

    hw = connection._hw_sim

    # Set sensor values
    with hw.lock:
        hw._sensors[SensorType.GPS].set_value((11, 12, 13))

    # Wait a few update cycles to flush any old packets out
    for i in range(2):
        snapshot = get_event_stats_snapshot()
        assert SENSOR_READ_EVENT.wait(snapshot) >= 1
        assert BULK_SENSOR_EVENT.wait(snapshot) >= 1
        assert BUNDLE_ADDED_EVENT.wait(snapshot) >= 1

    assert main_window.rocket_data.lastvalue(SubpacketEnum.LATITUDE.value) == 11
    assert main_window.rocket_data.lastvalue(SubpacketEnum.LONGITUDE.value) == 12

    # Set new sensor values
    with hw.lock:
        hw._sensors[SensorType.GPS].set_value((21, 22, 23))

    # Wait a few update cycles to flush any old packets out
    for i in range(2):
        snapshot = get_event_stats_snapshot()
        assert SENSOR_READ_EVENT.wait(snapshot) >= 1
        assert BULK_SENSOR_EVENT.wait(snapshot) >= 1
        assert BUNDLE_ADDED_EVENT.wait(snapshot) >= 1

    assert main_window.rocket_data.lastvalue(SubpacketEnum.LATITUDE.value) == 21
    assert main_window.rocket_data.lastvalue(SubpacketEnum.LONGITUDE.value) == 22
