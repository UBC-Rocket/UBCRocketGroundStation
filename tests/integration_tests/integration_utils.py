import pytest
import logging
from typing import List, Tuple

from main_window.data_entry_id import DataEntryIds
from profiles.rocket_profile_list import ROCKET_PROFILES, RocketProfile
from main_window.main_app import MainApp
from main_window.device_manager import DeviceType, DEVICE_REGISTERED_EVENT, is_device_type_flare
from main_window.read_thread import CONNECTION_MESSAGE_READ_EVENT
from main_window.rocket_data import BUNDLE_ADDED_EVENT

from util.event_stats import get_event_stats_snapshot


@pytest.fixture(scope="function")
def test_app(caplog):
    """
    Provides factory for constructing an instance of main_app for tests. Ensures that main_app is ready before starting
    test and shutdown after test is complete.

    :param caplog: fixture
    :return: Function handle to factory
    """

    app = None

    def construct(profile, connections, num_devices=None):
        nonlocal app
        snapshot = get_event_stats_snapshot()
        app = profile.construct_app(connections)

        if num_devices is None:
            expected = len(profile.expected_devices)
        else:
            expected = num_devices

        assert DEVICE_REGISTERED_EVENT.wait(snapshot, num_expected=expected) == expected

        return app

    yield construct

    # ----- Following code is run on cleanup -----

    if app is not None:
        app.shutdown()

    # Fail test if error message in logs since we catch most exceptions in app
    for when in ("setup", "call"):
        messages = [x.message for x in caplog.get_records(when) if x.levelno == logging.ERROR]
        if messages:
            pytest.fail(f"Errors reported in logs: {messages}")


def flush_packets(main_app: MainApp, device_type: DeviceType):
    """
    Wait a few update cycles to flush any old packets out

    :param rocket_data:
    :param device_type:
    :return:
    """

    received = 0
    last_time = 0
    while received < 5:
        snapshot = get_event_stats_snapshot()
        assert BUNDLE_ADDED_EVENT.wait(snapshot) >= 1
        assert CONNECTION_MESSAGE_READ_EVENT.wait(snapshot) >= 1

        # To ensure that we're only considering packets from specific device
        new_time = main_app.rocket_data.last_value_by_device(device_type, DataEntryIds.TIME)
        if new_time != last_time:  # No guarantee that packets come in chronological order
            received += 1
            last_time = new_time

def all_profiles(excluding: List[str] = []) -> List[RocketProfile]:
    """
    Returns a list of all rocket profiles excluding those indicated

    :param excluding: String name of rocket profiles to exclude from list
    :return:
    """

    return [profile for profile in ROCKET_PROFILES if profile.__class__.__name__ not in excluding]


def all_devices(excluding: List[DeviceType] = []) -> List[DeviceType]:
    """
    Returns a list of all DeviceTypes excluding those indicated

    :param excluding: DeviceTypes to exclude from list
    :return:
    """

    return [device for device in DeviceType if device not in excluding]


def only_flare(device_types: List[DeviceType]) -> List[DeviceType]:
    """
    Filters out non-flare device types

    :param device_types:
    :return: Filtered list of device types
    """

    return [device for device in device_types if is_device_type_flare(device)]


def valid_paramitrization(rocket_profiles: List[RocketProfile], device_types: List[DeviceType] = None) -> List[Tuple]:
    """
    Returns valid pytest parametrization combinations taking into account which profiles expect which device_types

    :param rocket_profiles:
    :param device_types:
    :return: Valid pytest parametrization combinations
    """

    params = []
    for profile in rocket_profiles:
        if device_types is None:
            params.append(pytest.param(profile, id=profile.__class__.__name__))
        else:
            for device in device_types:
                if device in profile.expected_devices:
                    params.append(pytest.param(profile, device, id=f"{profile.__class__.__name__}-{device.name}"))
    return params


