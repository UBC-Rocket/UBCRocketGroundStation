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
    TANTALUS_STAGE_1 = auto()
    TANTALUS_STAGE_2 = auto()
    CO_PILOT = auto()


class DeviceManager:

    def __init__(self, required_versions: Dict[DeviceType, str], strict_versions=True):
        self.required_versions = required_versions
        self.strict_versions = strict_versions

        self._lock = RLock()

        self._device_type_to_device: Dict[DeviceType, RegisteredDevice] = dict()
        self._full_address_to_device: Dict[FullAddress, RegisteredDevice] = dict()

    def register_device(self, device_type: DeviceType, device_version: str, full_address: FullAddress) -> None:
        with self._lock:
            if device_type not in self._device_type_to_device.keys() and full_address not in self._full_address_to_device.keys():
                pass

            elif device_type in self._device_type_to_device.keys() and full_address != self._device_type_to_device[device_type].full_address:
                raise InvalidRegistration(
                    f"Cannot reassign device_type={device_type.name} (full_address={self._device_type_to_device[device_type].full_address}) to full_address={full_address}")

            elif full_address in self._full_address_to_device.keys() and device_type != self._full_address_to_device[full_address].device_type:
                raise InvalidRegistration(
                    f"Cannot reassign full_address={full_address} (device={self._full_address_to_device[full_address].device_type}) to device={device_type}")

            else:
                LOGGER.info(f"Already registered. Device={device_type.name}, full_address={full_address}")
                return

            if device_type in self.required_versions.keys() and device_version != self.required_versions[device_type]:
                error_str = f"Version {device_version} does not match required version {self.required_versions[device_type]} for device {device_type.name}"
                if self.strict_versions:
                    raise InvalidDeviceVersion(error_str)
                else:
                    LOGGER.warning(error_str)

            self._device_type_to_device[device_type] = RegisteredDevice(device_type=device_type, full_address=full_address)
            self._full_address_to_device = {d.full_address: d for d in self._device_type_to_device.values()}

            # If two devices somehow have the same full address, mapping wont be one-to-one.
            assert len(self._device_type_to_device) == len(self._full_address_to_device)

            LOGGER.info(f"Registered device={device_type.name}, full_address={full_address}")
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


class InvalidRegistration(Exception):
    pass

class InvalidDeviceVersion(Exception):
    pass
