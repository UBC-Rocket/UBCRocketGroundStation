from enum import Enum, auto
from threading import RLock
from typing import Iterable
from util.detail import LOGGER
from util.event_stats import Event
from connections.connection import Connection

DEVICE_REGISTERED_EVENT = Event('device_registered')


class DeviceType(Enum):
    TANTALUS_STAGE_1 = auto()
    TANTALUS_STAGE_2 = auto()
    CO_PILOT = auto()


class DeviceManager:

    def __init__(self):
        self._lock = RLock()

        # One-to-one mapping
        self._device_to_hwid = dict()
        self._hwid_to_device = dict()

        # Many-to-one mapping
        self._hwid_to_connection = dict()

    def register_device(self, device: DeviceType, hwid: str, connection: Connection) -> None:
        with self._lock:
            if device not in self._device_to_hwid.keys() and hwid not in self._hwid_to_connection.keys():
                pass
            elif device in self._device_to_hwid.keys() and hwid != self._device_to_hwid[device]:
                raise InvalidRegistration(
                    f"Cannot reassign device={device.name} (HWID={self._device_to_hwid[device]}) to HWID={hwid}")
            elif hwid in self._hwid_to_device.keys() and device != self._hwid_to_device[hwid]:
                raise InvalidRegistration(
                    f"Cannot reassign HWID={hwid} (device={self._hwid_to_device[hwid]}) to device={device}")
            elif hwid in self._hwid_to_connection.keys() and self._hwid_to_connection[hwid] != connection:
                LOGGER.warning(
                    f"HWID={hwid} (connection={self._hwid_to_connection[hwid]}) is being re associated with to connection={connection}")
            else:
                LOGGER.info(f"Already registered. Device={device.name}, HWID={hwid}, connection={connection}")
                return

            self._device_to_hwid[device] = hwid
            self._hwid_to_device = {y: x for (x, y) in self._device_to_hwid.items()}

            self._hwid_to_connection[hwid] = connection

            LOGGER.info(f"Registered device={device.name}, HWID={hwid}, connection={connection}")
            DEVICE_REGISTERED_EVENT.increment()

    def get_connection(self, hwid: str) -> Connection:
        with self._lock:
            if hwid not in self._hwid_to_connection:
                return None
            return self._hwid_to_connection[hwid]

    def get_hwid(self, device: DeviceType) -> str:
        with self._lock:
            if device not in self._device_to_hwid:
                return None
            return self._device_to_hwid[device]

    def get_device(self, hwid: str) -> DeviceType:
        with self._lock:
            if hwid not in self._hwid_to_device:
                return None
            return self._hwid_to_device[hwid]

    def get_registered_device(self) -> Iterable[DeviceType]:
        with self._lock:
            return self._device_to_hwid.keys()


class InvalidRegistration(Exception):
    pass
