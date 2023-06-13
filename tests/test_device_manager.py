import pytest
from main_window.device_manager import DeviceManager, DeviceType, FullAddress, InvalidRegistration, InvalidDeviceVersion, DEVICE_REGISTERED_EVENT
from util.event_stats import get_event_stats_snapshot


def test_normal_registration():
    device_manager = DeviceManager(None, None)

    full_address_1 = FullAddress(connection_name='BNBStage1Connection', device_address='BNBStage1Address')
    full_address_2 = FullAddress(connection_name='BNBStage2Connection', device_address='BNBStage2Address')

    snapshot = get_event_stats_snapshot()
    device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, None, full_address_1)
    device_manager.register_device(DeviceType.BNB_STAGE_2_FLARE, None, full_address_2)

    assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=2, timeout=0) == 2
    assert device_manager.get_full_address(DeviceType.BNB_STAGE_1_FLARE) == full_address_1
    assert device_manager.get_full_address(DeviceType.BNB_STAGE_2_FLARE) == full_address_2



def test_existing_device():
    device_manager = DeviceManager(None, None)
    full_address_1 = FullAddress(connection_name='BNBStage1Connection', device_address='BNBStage1Address')
    full_address_2 = FullAddress(connection_name='BNBStage2Connection', device_address='BNBStage2Address')
    device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, None, full_address_1)

    with pytest.raises(InvalidRegistration):
        device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, None, full_address_2)

    assert device_manager.get_full_address(DeviceType.BNB_STAGE_1_FLARE) == full_address_1


def test_existing_full_address():
    device_manager = DeviceManager(None, None)
    full_address_1 = FullAddress(connection_name='BNBStage1Connection', device_address='BNBStage1Address')
    device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, None, full_address_1)

    with pytest.raises(InvalidRegistration):
        device_manager.register_device(DeviceType.BNB_STAGE_2_FLARE, None, full_address_1)

    assert device_manager.get_full_address(DeviceType.BNB_STAGE_1_FLARE) == full_address_1

def test_wrong_version():
    device_manager = DeviceManager(None, {DeviceType.BNB_STAGE_1_FLARE: 'RequiredVersion'})
    full_address_1 = FullAddress(connection_name='BNBStage1Connection', device_address='BNBStage1Address')

    with pytest.raises(InvalidDeviceVersion):
        device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, 'OtherVersion', full_address_1)

    assert device_manager.get_full_address(DeviceType.BNB_STAGE_1_FLARE) is None

def test_num_expected():
    device_manager = DeviceManager([DeviceType.BNB_STAGE_1_FLARE], None)
    full_address_1 = FullAddress(connection_name='BNBStage1Connection', device_address='BNBStage1Address')
    full_address_2 = FullAddress(connection_name='BNBStage2Connection', device_address='BNBStage2Address')

    device_manager.register_device(DeviceType.BNB_STAGE_2_FLARE, None, full_address_2)
    assert device_manager.num_expected_registered() == 0

    device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, None, full_address_1)
    assert device_manager.num_expected_registered() == 1
