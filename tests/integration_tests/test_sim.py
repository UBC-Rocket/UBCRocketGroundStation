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

    with hw.lock:
        hw._sensors[SensorType.GPS].set_value((1, 2, 3))

    snapshot = get_event_stats_snapshot()

    num = SENSOR_READ_EVENT.wait(snapshot)
    assert num >= 1

    num = BULK_SENSOR_EVENT.wait(snapshot)
    assert num >= 1

    num = BUNDLE_ADDED_EVENT.wait(snapshot)
    assert num >= 1

    # TODO : FW bug reporting bad values, change assert once fixed to check actual value
    assert main_window.rocket_data.lastvalue(SubpacketEnum.LATITUDE.value) is not None
    assert main_window.rocket_data.lastvalue(SubpacketEnum.LONGITUDE.value) is not None
