from enum import Enum, auto
from threading import RLock
from typing import Iterable, List, Dict
from collections import namedtuple
from util.detail import LOGGER
from util.event_stats import Event
from connections.connection import Connection

DEVICE_REGISTERED_EVENT = Event('device_registered')

# For internal use only
RegisteredDevice = namedtuple('RegisteredDevice', ['hwid', 'device_type', 'connection'])

class DeviceType(Enum):
    TANTALUS_STAGE_1 = auto()
    TANTALUS_STAGE_2 = auto()
    CO_PILOT = auto()


class DeviceManager:

    def __init__(self):
        self._lock = RLock()

        self._device_type_to_device: Dict[DeviceType, RegisteredDevice] = dict()
        self._hwid_to_device: Dict[str, RegisteredDevice] = dict()

    def register_device(self, device_type: DeviceType, hwid: str, connection: Connection) -> None:
        with self._lock:
            if device_type not in self._device_type_to_device.keys() and hwid not in self._hwid_to_device.keys():
                pass

            elif device_type in self._device_type_to_device.keys() and hwid != self._device_type_to_device[device_type].hwid:
                raise InvalidRegistration(
                    f"Cannot reassign device={device_type.name} (HWID={self._device_type_to_device[device_type].hwid}) to HWID={hwid}")

            elif hwid in self._hwid_to_device.keys() and device_type != self._hwid_to_device[hwid].device_type:
                raise InvalidRegistration(
                    f"Cannot reassign HWID={hwid} (device={self._hwid_to_device[hwid].device_type}) to device={device_type}")

            elif hwid in self._hwid_to_device.keys() and self._hwid_to_device[hwid].connection != connection:
                LOGGER.warning(
                    f"HWID={hwid} (connection={self._hwid_to_device[hwid].connection}) is being re associated with to connection={connection}")

            else:
                LOGGER.info(f"Already registered. Device={device_type.name}, HWID={hwid}, connection={connection}")
                return

            self._device_type_to_device[device_type] = RegisteredDevice(hwid=hwid, device_type=device_type, connection=connection)
            self._hwid_to_device = {d.hwid: d for d in self._device_type_to_device.values()}

            LOGGER.info(f"Registered device={device_type.name}, HWID={hwid}, connection={connection}")
            DEVICE_REGISTERED_EVENT.increment()

    def get_connection(self, hwid: str) -> Connection:
        with self._lock:
            if hwid not in self._hwid_to_device:
                return None
            return self._hwid_to_device[hwid].connection

    def get_hwid(self, device: DeviceType) -> str:
        with self._lock:
            if device not in self._device_type_to_device:
                return None
            return self._device_type_to_device[device].hwid

    def get_device(self, hwid: str) -> DeviceType:
        with self._lock:
            if hwid not in self._hwid_to_device:
                return None
            return self._hwid_to_device[hwid].device_type

    def get_registered_devices(self) -> Iterable[DeviceType]:
        with self._lock:
            return self._device_type_to_device.keys()


class InvalidRegistration(Exception):
    pass
