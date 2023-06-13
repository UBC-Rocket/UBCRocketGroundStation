from enum import Enum, auto
from threading import RLock
from typing import Iterable, List, Dict
from collections import namedtuple
from util.detail import LOGGER
from util.event_stats import Event

DEVICE_REGISTERED_EVENT = Event('device_registered')

FullAddress = namedtuple('FullAddress', ['connection_name', 'device_address'])
RegisteredDevice = namedtuple('RegisteredDevice', ['device_type', 'full_address'])


class DeviceType(Enum):
    BNB_STAGE_1_FLARE = auto()
    BNB_STAGE_2_FLARE = auto()
    CO_PILOT_FLARE = auto()
    HOLLYBURN_BODY_FLARE = auto()
    HOLLYBURN_NOSE_FLARE = auto()
    SILVERTIP_FLARE = auto()


_FLARE_DEVICE_TYPES = [
    DeviceType.BNB_STAGE_1_FLARE,
    DeviceType.BNB_STAGE_2_FLARE,
    DeviceType.CO_PILOT_FLARE,
    DeviceType.HOLLYBURN_BODY_FLARE,
    DeviceType.HOLLYBURN_NOSE_FLARE,
    DeviceType.SILVERTIP_FLARE,
]


def is_device_type_flare(device_type: DeviceType):
    return device_type in _FLARE_DEVICE_TYPES


class DeviceManager:

    def __init__(self, expected_devices: List[DeviceType], required_versions: Dict[DeviceType, str],
                 strict_versions=True):

        if expected_devices is None:
            self.expected_devices = []
        else:
            self.expected_devices = expected_devices

        if required_versions is None:
            self.required_versions = dict()
        else:
            self.required_versions = required_versions

        self.strict_versions = strict_versions

        self._lock = RLock()

        self._device_type_to_device: Dict[DeviceType, RegisteredDevice] = dict()
        self._full_address_to_device: Dict[FullAddress, RegisteredDevice] = dict()

    def register_device(self, device_type: DeviceType, device_version: str, full_address: FullAddress) -> None:
        with self._lock:
            if device_type not in self._device_type_to_device and full_address not in self._full_address_to_device:
                pass

            elif device_type in self._device_type_to_device and full_address != self._device_type_to_device[
                device_type].full_address:
                raise InvalidRegistration(
                    f"Cannot reassign device_type={device_type.name} (full_address={self._device_type_to_device[device_type].full_address}) to full_address={full_address}")

            elif full_address in self._full_address_to_device and device_type != self._full_address_to_device[
                full_address].device_type:
                raise InvalidRegistration(
                    f"Cannot reassign full_address={full_address} (device={self._full_address_to_device[full_address].device_type}) to device={device_type}")

            else:
                LOGGER.info(f"Already registered. Device={device_type.name}, full_address={full_address}")
                return

            if device_type in self.required_versions and device_version != self.required_versions[device_type]:
                error_str = f"Version {device_version} does not match required version {self.required_versions[device_type]} for device {device_type.name}"
                if self.strict_versions:
                    raise InvalidDeviceVersion(error_str)
                else:
                    LOGGER.warning(error_str)

            self._device_type_to_device[device_type] = RegisteredDevice(device_type=device_type,
                                                                        full_address=full_address)
            self._full_address_to_device = {d.full_address: d for d in self._device_type_to_device.values()}

            # If two devices somehow have the same full address, mapping wont be one-to-one.
            assert len(self._device_type_to_device) == len(self._full_address_to_device)

            if device_type in self.expected_devices:
                LOGGER.info(
                    f"Registered expected device={device_type.name}, full_address={full_address}, {self.num_expected_registered()}/{len(self.expected_devices)} expected devices")
            else:
                LOGGER.warning(
                    f"Registered unexpected device={device_type.name}, full_address={full_address}, {self.num_expected_registered()}/{len(self.expected_devices)} expected devices")

            DEVICE_REGISTERED_EVENT.increment()

    def get_full_address(self, device_type: DeviceType) -> FullAddress:
        with self._lock:
            if device_type not in self._device_type_to_device:
                return None
            return self._device_type_to_device[device_type].full_address

    def get_device_type(self, full_address: FullAddress) -> DeviceType:
        with self._lock:
            if full_address not in self._full_address_to_device:
                return None
            return self._full_address_to_device[full_address].device_type

    def num_expected_registered(self):
        with self._lock:
            count = 0

            for device_type in self._device_type_to_device:
                if device_type in self.expected_devices:
                    count += 1

        return count


class InvalidRegistration(Exception):
    pass


class InvalidDeviceVersion(Exception):
    pass
