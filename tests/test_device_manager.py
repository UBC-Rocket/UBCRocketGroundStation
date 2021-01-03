import pytest
from main_window.device_manager import DeviceManager, DeviceType, FullAddress, InvalidRegistration, InvalidDeviceVersion, DEVICE_REGISTERED_EVENT
from util.event_stats import get_event_stats_snapshot


def test_normal_registration():
    device_manager = DeviceManager(dict())

    full_address_1 = FullAddress(connection_name='TantalusStage1Connection', device_address='TantalusStage1Address')
    full_address_2 = FullAddress(connection_name='TantalusStage2Connection', device_address='TantalusStage2Address')

    snapshot = get_event_stats_snapshot()
    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, None, full_address_1)
    device_manager.register_device(DeviceType.TANTALUS_STAGE_2, None, full_address_2)

    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=2, timeout=0) == 2
    assert device_manager.get_full_address(DeviceType.TANTALUS_STAGE_1) == full_address_1
    assert device_manager.get_full_address(DeviceType.TANTALUS_STAGE_2) == full_address_2



def test_existing_device():
    device_manager = DeviceManager(dict())
    full_address_1 = FullAddress(connection_name='TantalusStage1Connection', device_address='TantalusStage1Address')
    full_address_2 = FullAddress(connection_name='TantalusStage2Connection', device_address='TantalusStage2Address')
    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, None, full_address_1)

    with pytest.raises(InvalidRegistration):
        device_manager.register_device(DeviceType.TANTALUS_STAGE_1, None, full_address_2)

    assert device_manager.get_full_address(DeviceType.TANTALUS_STAGE_1) == full_address_1


def test_existing_full_address():
    device_manager = DeviceManager(dict())
    full_address_1 = FullAddress(connection_name='TantalusStage1Connection', device_address='TantalusStage1Address')
    device_manager.register_device(DeviceType.TANTALUS_STAGE_1, None, full_address_1)

    with pytest.raises(InvalidRegistration):
        device_manager.register_device(DeviceType.TANTALUS_STAGE_2, None, full_address_1)

    assert device_manager.get_full_address(DeviceType.TANTALUS_STAGE_1) == full_address_1

def test_wrong_version():
    device_manager = DeviceManager({DeviceType.TANTALUS_STAGE_1: 'RequiredVersion'})
    full_address_1 = FullAddress(connection_name='TantalusStage1Connection', device_address='TantalusStage1Address')

    with pytest.raises(InvalidDeviceVersion):
        device_manager.register_device(DeviceType.TANTALUS_STAGE_1, 'OtherVersion', full_address_1)

    assert device_manager.get_full_address(DeviceType.TANTALUS_STAGE_1) is None
