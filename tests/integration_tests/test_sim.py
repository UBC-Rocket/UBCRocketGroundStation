import pytest
from connections.sim.sim_connection_factory import SimConnectionFactory, FirmwareNotFound
from connections.sim.hw_sim import SensorType, SENSOR_READ_EVENT
from main_window.main import MainApp
from profiles.rockets.tantalus import TantalusProfile
from main_window.rocket_data import BUNDLE_ADDED_EVENT
from main_window.subpacket_ids import SubpacketEnum
from main_window.radio_controller import BULK_SENSOR_EVENT

from util.event_stats import get_event_stats_snapshot


@pytest.fixture(scope="function")
def main_app() -> MainApp:
    try:
        connection = SimConnectionFactory().construct(rocket=TantalusProfile())
    except FirmwareNotFound as ex:
        pytest.skip("Firmware not found")
    app = MainApp(connection, TantalusProfile())
    yield app  # Provides app, following code is run on cleanup
    app.shutdown()

def test_gps_read(qtbot, main_app):
    connection = main_app.connection

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

    assert main_app.rocket_data.lastvalue(SubpacketEnum.LATITUDE.value) == 11
    assert main_app.rocket_data.lastvalue(SubpacketEnum.LONGITUDE.value) == 12

    # Set new sensor values
    with hw.lock:
        hw._sensors[SensorType.GPS].set_value((21, 22, 23))

    # Wait a few update cycles to flush any old packets out
    for i in range(2):
        snapshot = get_event_stats_snapshot()
        assert SENSOR_READ_EVENT.wait(snapshot) >= 1
        assert BULK_SENSOR_EVENT.wait(snapshot) >= 1
        assert BUNDLE_ADDED_EVENT.wait(snapshot) >= 1

    assert main_app.rocket_data.lastvalue(SubpacketEnum.LATITUDE.value) == 21
    assert main_app.rocket_data.lastvalue(SubpacketEnum.LONGITUDE.value) == 22


def test_clean_shutdown(qtbot, main_app):
    assert main_app.ReadThread.isRunning()
    assert main_app.SendThread.isRunning()
    assert main_app.MappingThread.isRunning()
    assert main_app.rocket_data.autosaveThread.is_alive()
    assert main_app.connection.thread.is_alive()
    assert main_app.connection._xbee._rocket_rx_thread.is_alive()

    main_app.shutdown()

    assert main_app.ReadThread.isFinished()
    assert main_app.SendThread.isFinished()
    assert main_app.MappingThread.isFinished()
    assert not main_app.rocket_data.autosaveThread.is_alive()
    assert not main_app.connection.thread.is_alive()
    assert not main_app.connection._xbee._rocket_rx_thread.is_alive()
