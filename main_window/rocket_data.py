import os
import threading
from typing import Dict, Union, Set, Callable, List
from collections import namedtuple

import numpy as np

from util.detail import LOGS_DIR, SESSION_ID, LOGGER
from util.event_stats import Event
from .data_entry_id import DataEntryIds
from .device_manager import DeviceManager, DeviceType, FullAddress

BUNDLE_ADDED_EVENT = Event('bundle_added')

DataEntryKey = namedtuple('DataEntry', ['full_address', 'data_id'])
CallBackKey = namedtuple('DataEntry', ['device', 'data_id'])

AUTOSAVE_INTERVAL_S = 10

class RocketData:
    def __init__(self, device_manager: DeviceManager) -> None:
        """
        Timeset is dictionary of all of the time points mapped to a dictionary of DataEntryKey -> value.
        """
        self.device_manager = device_manager

        self.data_lock = threading.RLock()  # create lock ASAP since self.lock needs to be defined when autosave starts
        self.timeset: Dict[int, Dict[DataEntryKey, Union[int, float, str]]] = {}
        self.last_time = 0
        self.highest_altitude: float = 0 # TODO Implement actual logic
        self.session_name = os.path.join(LOGS_DIR, "autosave_" + SESSION_ID + ".csv")
        self.existing_entry_keys: Set[DataEntryKey] = set() # Set of entry keys that have actually been recorded. Used for creating csv header

        self.callback_lock = threading.RLock()  # Only for callback dict
        self.callbacks: Dict[CallBackKey, List[Callable]] = {}

        self.as_cv = threading.Condition()  # Condition variable for autosave (as)
        self._as_is_shutting_down = False  # Lock in cv is used to protect this

        self.autosave_thread = threading.Thread(target=self.timer, daemon=True, name="AutosaveThread")
        self.autosave_thread.start()

    def timer(self):
        """

        """
        LOGGER.debug("Auto-save thread started")
        while True:

            with self.as_cv:
                self.as_cv.wait_for(lambda: self._as_is_shutting_down, timeout=AUTOSAVE_INTERVAL_S)

                if self._as_is_shutting_down:
                    break

            try:
                self.save(self.session_name)
                LOGGER.debug("Auto-Save successful.")
            except Exception as e:
                LOGGER.exception("Exception in autosave thread")  # Automatically grabs and prints exception info

        LOGGER.warning("Auto save thread shut down")

    def shutdown(self):
        with self.as_cv:
            self._as_is_shutting_down = True

        while self.autosave_thread.is_alive():
            with self.as_cv:
                self.as_cv.notify()  # Wake up thread

        self.autosave_thread.join()  # join thread

    def add_bundle(self, full_address: FullAddress, incoming_data: Dict[DataEntryIds, any]):
        """
        Adding a bundle of data points and trigger callbacks according to id.
        Current implementation: adds to time given, otherwise will add to the last time received.

        :param incoming_data:
        :type incoming_data:
        """
        with self.data_lock:
            # if there's a time, set this to the most recent time val
            if DataEntryIds.TIME in incoming_data:
                self.last_time = incoming_data[DataEntryIds.TIME]
            # if the timeset then setup a respective dict for the data
            if self.last_time not in self.timeset:
                self.timeset[self.last_time] = {}

            # write the data and call the respective callbacks
            for data_id in incoming_data:
                key = DataEntryKey(full_address, data_id)
                self.existing_entry_keys.add(key)
                self.timeset[self.last_time][key] = incoming_data[data_id]

        device = self.device_manager.get_device_type(full_address)
        if device is not None:
            # Notify after all data has been updated
            # Also, do so outside data_lock to prevent mutex contention with notification listeners
            for data_id in incoming_data:
                key = CallBackKey(device, data_id)
                self._notify_callbacks_of_id(key)

        BUNDLE_ADDED_EVENT.increment()

    def last_value_by_device(self, device: DeviceType, sensor_id: DataEntryIds):
        """
        Gets the most recent value specified by the DataEntryIds (enum object) given

        :param device:
        :type device:
        :param sensor_id:
        :type sensor_id:
        :return:
        :rtype:
        """
        with self.data_lock:
            times = list(self.timeset.keys())
            times.sort(reverse=True) # TODO : Should probably use OrderedDict to improve performance

            full_address = self.device_manager.get_full_address(device)
            if full_address is None:
                return None

            data_entry_key = DataEntryKey(full_address, sensor_id)
            for i in range(len(times)):
                if data_entry_key in self.timeset[times[i]]:
                    return self.timeset[times[i]][data_entry_key]
            return None

    def save(self, csv_path):
        """
        Data saving function that creates csv

        :param csv_path:
        :type csv_path:
        :return:
        :rtype:
        """
        with self.data_lock:
            if len(self.timeset) <= 0:
                return

            # all appearing keys
            keys: List[DataEntryKey] = list(map(
                lambda data_entry_key: DataEntryKey(data_entry_key.full_address, data_entry_key.data_id),
                self.existing_entry_keys))

            data = np.empty((len(keys), len(self.timeset) + 1), dtype=object)
            times = list(self.timeset.keys())
            times.sort(reverse=False)
            for ix, iy in np.ndindex(data.shape):
                # Make the first row a list of sensor names. Use the enum's name property
                if iy == 0:
                    data_name = keys[ix].data_id.name if isinstance(keys[ix].data_id, DataEntryIds) else str(keys[ix].data_id)
                    device = self.device_manager.get_device_type(keys[ix].full_address)
                    if device:
                        device_name = device.name
                    else:
                        device_name = f"{keys[ix].full_address.connection_name}_{keys[ix].full_address.device_address}"

                    data[ix, iy] = data_name + '_' + device_name
                else:
                    if keys[ix].data_id == DataEntryIds.TIME:
                        data[ix, iy] = times[iy - 1]
                    else:
                        if keys[ix] in self.timeset[times[iy - 1]]:
                            data[ix, iy] = self.timeset[times[iy - 1]][keys[ix]]
                        else:
                            data[ix, iy] = ""

        np.savetxt(csv_path, np.transpose(data), delimiter=',',
                   fmt="%s")  # Can free up the lock while we save since were no longer accessing the original data

    def add_new_callback(self, device: DeviceType, data_id: DataEntryIds, callback_fn: Callable):
        """
        Add a new callback for its associated ID

        :param device:
        :type device:
        :param data_id:
        :type data_id:
        :param callback_fn:
        :type callback_fn:
        """
        with self.callback_lock:
            key = CallBackKey(device, data_id)
            if key not in self.callbacks:
                self.callbacks[key] = [callback_fn]
            else:
                self.callbacks[key].append(callback_fn)

    def _notify_callbacks_of_id(self, key: CallBackKey):
        """

        :param data_id:
        :type data_id:
        """
        with self.callback_lock:
            if key in self.callbacks:
                for fn in self.callbacks[key]:
                    fn()

    def _notify_all_callbacks(self):
        """

        """
        with self.callback_lock:
            for key in self.callbacks:
                self._notify_callbacks_of_id(key)
