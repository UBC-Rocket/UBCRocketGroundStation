import pytest

from main_window.data_entry_id import DataEntryIds
from main_window.device_manager import DeviceManager, DeviceType
from main_window.rocket_data import RocketData, DataEntryKey


@pytest.fixture(scope="function")
def full_device_manager():
    device_manager = DeviceManager(None, None)
    for device in DeviceType:
        device_manager.register_device(device, None, ('CONNECTION', device.name))
    return device_manager


@pytest.fixture()
def bulk_sensor_bundle():
    return {
        DataEntryIds.TIME: 0,
        DataEntryIds.CALCULATED_ALTITUDE: 1,
        DataEntryIds.ACCELERATION_X: 2,
        DataEntryIds.ACCELERATION_Y: 3,
        DataEntryIds.ACCELERATION_Z: 4,
        DataEntryIds.ORIENTATION_1: 5,
        DataEntryIds.ORIENTATION_2: 6,
        DataEntryIds.ORIENTATION_3: 7,
        DataEntryIds.LATITUDE: 8,
        DataEntryIds.LONGITUDE: 9,
        DataEntryIds.STATE: 10,
        DataEntryIds.DEVICE_TYPE: DeviceType.BNB_STAGE_1_FLARE,
        # DataEntryIds.VERSION_ID: REQUIRED_FLARE,
    }


@pytest.fixture(scope="function")
def rocket_data_with_bulk_added(full_device_manager, bulk_sensor_bundle):
    rocket_data = RocketData(full_device_manager)
    bulk_address = full_device_manager.get_full_address(bulk_sensor_bundle[DataEntryIds.DEVICE_TYPE])
    rocket_data.add_bundle(bulk_address, bulk_sensor_bundle)
    return rocket_data, bulk_address


def test_timer():
    pass  # TODO


def test_shutdown():
    pass  # TODO


def test_add_bundle(full_device_manager, rocket_data_with_bulk_added, bulk_sensor_bundle):
    rocket_data, full_address = rocket_data_with_bulk_added

    # Manual inspection, in order to check add_bundle without last_value dependency
    for key, val in bulk_sensor_bundle.items():
        data_entry = DataEntryKey(full_address, key)
        assert rocket_data.keyset[data_entry] is not None
        assert rocket_data.keyset[data_entry].peekitem()[1] == val

    # TODO Check callbacks
    return


def test_time_series_by_device():
    pass  # TODO


def test_last_value_and_time():
    pass  # TODO


def test_last_value_by_device(full_device_manager, rocket_data_with_bulk_added, bulk_sensor_bundle):
    rocket_data, full_address = rocket_data_with_bulk_added

    for key, val in bulk_sensor_bundle.items():
        assert rocket_data.last_value_by_device(DeviceType.BNB_STAGE_1_FLARE, key) == val
    return


def test_highest_altitude_by_device_single(full_device_manager, rocket_data_with_bulk_added):
    rocket_data, full_address = rocket_data_with_bulk_added
    altitude_bundle = {
        DataEntryIds.TIME: 5,
        DataEntryIds.CALCULATED_ALTITUDE: 1234,
        DataEntryIds.DEVICE_TYPE: DeviceType.BNB_STAGE_2_FLARE,
        # DataEntryIds.VERSION_ID: REQUIRED_FLARE,
    }
    full_address_stage_2 = full_device_manager.get_full_address(altitude_bundle[DataEntryIds.DEVICE_TYPE])
    rocket_data.add_bundle(full_address_stage_2, altitude_bundle)

    assert rocket_data.highest_altitude[full_address_stage_2] == altitude_bundle[DataEntryIds.CALCULATED_ALTITUDE]
    assert rocket_data.last_value_by_device(
        altitude_bundle[DataEntryIds.DEVICE_TYPE],
        DataEntryIds.CALCULATED_ALTITUDE
    ) == altitude_bundle[DataEntryIds.CALCULATED_ALTITUDE]


def test_highest_altitude_by_device_multiple(full_device_manager, rocket_data_with_bulk_added, bulk_sensor_bundle):
    rocket_data, full_address = rocket_data_with_bulk_added
    altitude_bundle = {
        DataEntryIds.TIME: 5,
        DataEntryIds.CALCULATED_ALTITUDE: 1234,
        DataEntryIds.DEVICE_TYPE: DeviceType.BNB_STAGE_2_FLARE,
        # DataEntryIds.VERSION_ID: REQUIRED_FLARE,
    }
    full_address_stage_2 = full_device_manager.get_full_address(altitude_bundle[DataEntryIds.DEVICE_TYPE])
    rocket_data.add_bundle(full_address_stage_2, altitude_bundle)

    # higher altitude bundle version
    altitude_bundle_2 = altitude_bundle.copy()
    altitude_bundle_2[DataEntryIds.TIME] = 99
    altitude_bundle_2[DataEntryIds.CALCULATED_ALTITUDE] = 9999
    full_address_stage_2 = full_device_manager.get_full_address(altitude_bundle_2[DataEntryIds.DEVICE_TYPE])
    rocket_data.add_bundle(full_address_stage_2, altitude_bundle_2)

    # altitude bundle
    assert rocket_data.highest_altitude[full_address_stage_2] == altitude_bundle_2[DataEntryIds.CALCULATED_ALTITUDE]
    assert rocket_data.last_value_by_device(
        altitude_bundle_2[DataEntryIds.DEVICE_TYPE],
        DataEntryIds.CALCULATED_ALTITUDE
    ) == altitude_bundle_2[DataEntryIds.CALCULATED_ALTITUDE]

    # bulk
    assert rocket_data.highest_altitude[full_address] == bulk_sensor_bundle[DataEntryIds.CALCULATED_ALTITUDE]
    assert rocket_data.last_value_by_device(
        bulk_sensor_bundle[DataEntryIds.DEVICE_TYPE],
        DataEntryIds.CALCULATED_ALTITUDE
    ) == bulk_sensor_bundle[DataEntryIds.CALCULATED_ALTITUDE]


def test_save():
    pass  # TODO


def test_add_new_callback():
    pass  # TODO


def test__notify_callbacks_of_id():
    pass  # TODO


def test__notify_all_callbacks():
    pass  # TODO
