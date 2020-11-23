import pytest
from main_window.device_manager import DeviceManager, DeviceType, InvalidRegistration, DEVICE_REGISTERED_EVENT
from util.event_stats import get_event_stats_snapshot


def test_normal_registration():
    device_manager = DeviceManager()

    snapshot = get_event_stats_snapshot()
    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'TantalusStage1HWID', 'TantalusStage1Connection')
    device_manager.register_device(DeviceType.TANTALUS_STAGE_2, 'TantalusStage2HWID', 'TantalusStage2Connection')
    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=2, timeout=0) == 2

    assert device_manager.get_hwid(DeviceType.TANTALUS_STAGE_1) == 'TantalusStage1HWID'
    assert device_manager.get_device('TantalusStage1HWID') == DeviceType.TANTALUS_STAGE_1
    assert device_manager.get_connection('TantalusStage1HWID') == 'TantalusStage1Connection'

    assert device_manager.get_hwid(DeviceType.TANTALUS_STAGE_1) == 'TantalusStage1HWID'
    assert device_manager.get_device('TantalusStage1HWID') == DeviceType.TANTALUS_STAGE_1
    assert device_manager.get_connection('TantalusStage1HWID') == 'TantalusStage1Connection'


def test_existing_device():
    device_manager = DeviceManager()

    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'TantalusStage1HWID', 'TantalusStage1Connection')

    with pytest.raises(InvalidRegistration):
        device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'TantalusStage2HWID', 'TantalusStage2Connection')

    assert device_manager.get_hwid(DeviceType.TANTALUS_STAGE_1) == 'TantalusStage1HWID'
    assert device_manager.get_device('TantalusStage1HWID') == DeviceType.TANTALUS_STAGE_1
    assert device_manager.get_connection('TantalusStage1HWID') == 'TantalusStage1Connection'


def test_existing_hwid():
    device_manager = DeviceManager()

    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'TantalusStage1HWID', 'TantalusStage1Connection')

    with pytest.raises(InvalidRegistration):
        device_manager.register_device(DeviceType.TANTALUS_STAGE_2, 'TantalusStage1HWID', 'TantalusStage2Connection')

    assert device_manager.get_hwid(DeviceType.TANTALUS_STAGE_1) == 'TantalusStage1HWID'
    assert device_manager.get_device('TantalusStage1HWID') == DeviceType.TANTALUS_STAGE_1
    assert device_manager.get_connection('TantalusStage1HWID') == 'TantalusStage1Connection'


def test_reassign_connection():
    device_manager = DeviceManager()

    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'TantalusStage1HWID', 'TantalusStage1Connection')
    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'TantalusStage1HWID', 'OtherTantalusStage1Connection')

    assert device_manager.get_hwid(DeviceType.TANTALUS_STAGE_1) == 'TantalusStage1HWID'
    assert device_manager.get_device('TantalusStage1HWID') == DeviceType.TANTALUS_STAGE_1
    assert device_manager.get_connection('TantalusStage1HWID') == 'OtherTantalusStage1Connection'
