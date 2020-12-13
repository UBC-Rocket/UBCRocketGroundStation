import os
import threading
from typing import Dict, Union
from collections import namedtuple

import numpy as np

from util.detail import LOGS_DIR, SESSION_ID, LOGGER
from util.event_stats import Event
from .data_entry_id import DataEntryIds
from .device_manager import DeviceManager, DeviceType, FullAddress

BUNDLE_ADDED_EVENT = Event('bundle_added')

# nametochar : Dict[str, bytes] = { # TODO Deal with legacy data types and conversions. Delete dead code when done.
#     "Acceleration X": b'X',
#     "Acceleration Y": b'Y',
#     "Acceleration Z": b'Z',
#     "Pressure": b'P',
#     "Barometer Temperature": b'~',
#     "Temperature": b'T',
#     "Yaw": b'@',
#     "Roll": b'#',
#     "Pitch": b'$',
#     "Latitude": b'L',
#     "Longitude": b'l',
#     "GPS Altitude": b'A',
#     "Calculated Altitude": b'a', # barometer altitude
#     "State": b's',
#     "Voltage": b'b',
#     "Ground Altitude": b'g',
#     "Time": b't',
#     "Orientation 1": b'o',
#     "Orientation 2": b'p',
#     "Orientation 3": b'q',
# }
#
# chartoname = {}
# for x in nametochar:
#     chartoname[nametochar[x]] = x
#
# orderednames = list(nametochar.keys())
# orderednames.sort()

# typemap = {  # TODO Review legacy data format
#     's': "state",
#     't': "int"
# }
#
# statemap = {  # TODO Review legacy data format. Not deleted due to need to confer with frontend
#     0: "STANDBY",
#     1: "ARMED",
#     2: "ASCENT",
#     3: "MACH_LOCK",
#     4: "PRESSURE_DELAY",
#     5: "INITIAL_DESCENT",
#     6: "FINAL_DESCENT",
#     7: "LANDED",
#     8: "WINTER_CONTINGENCY"
# }

DataEntryKey = namedtuple('DataEntry', ['full_address', 'data_id'])
CallBackKey = namedtuple('DataEntry', ['device', 'data_id'])

AUTOSAVE_INTERVAL_S = 10

class RocketData:
    def __init__(self, device_manager: DeviceManager) -> None:
        """
        Timeset is dictionary of all of the time points mapped to a dictionary of id -> value.
        """
        self.device_manager = device_manager

        self.data_lock = threading.RLock()  # create lock ASAP since self.lock needs to be defined when autosave starts
        self.timeset: Dict[int, Dict[DataEntryKey, Union[int, float]]] = {}
        self.lasttime = 0  # TODO REVIEW/CHANGE THIS, once all subpackets have their own timestamp.
        self.highest_altitude = 0
        self.sessionName = os.path.join(LOGS_DIR, "autosave_" + SESSION_ID + ".csv")
        self.existing_entry_keys = set() # Set of entry keys that have actually been recorded. Used for creating csv header

        self.callback_lock = threading.RLock()  # Only for callback dict
        self.callbacks = {}

        self.as_cv = threading.Condition()  # Condition variable for autosave (as)
        self._as_is_shutting_down = False  # Lock in cv is used to protect this

        self.autosaveThread = threading.Thread(target=self.timer, daemon=True, name="AutosaveThread")
        self.autosaveThread.start()

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
                self.save(self.sessionName)
                LOGGER.debug("Auto-Save successful.")
            except Exception as e:
                LOGGER.exception("Exception in autosave thread")  # Automatically grabs and prints exception info

        LOGGER.warning("Auto save thread shut down")

    def shutdown(self):
        with self.as_cv:
            self._as_is_shutting_down = True

        while self.autosaveThread.is_alive():
            with self.as_cv:
                self.as_cv.notify()  # Wake up thread

        self.autosaveThread.join()  # join thread

    # TODO Needs to use DataEntryId. Store Enum objects, not values
    # Adding a bundle of data points and trigger callbacks according to id.
    # Current implementation: adds to time given, otherwise will add to the last time received.
    def addBundle(self, full_address: FullAddress, incoming_data):
        """

        :param incoming_data:
        :type incoming_data:
        """
        with self.data_lock:
            # if there's a time, set this to the most recent time val
            if DataEntryIds.TIME in incoming_data.keys():
                self.lasttime = incoming_data[DataEntryIds.TIME]
            # if the timeset then setup a respective dict for the data
            if self.lasttime not in self.timeset.keys():
                self.timeset[self.lasttime] = {}

            # write the data and call the respective callbacks
            for data_id in incoming_data.keys():
                key = DataEntryKey(full_address, data_id)
                self.existing_entry_keys.add(key)
                self.timeset[self.lasttime][key] = incoming_data[data_id]

        device = self.device_manager.get_device_type(full_address)
        if device is not None:
            # Notify after all data has been updated
            # Also, do so outside data_lock to prevent mutex contention with notification listeners
            for data_id in incoming_data.keys():
                key = CallBackKey(device, data_id)
                self._notifyCallbacksOfId(key)

        BUNDLE_ADDED_EVENT.increment()

    # TODO update all calls. TODO write note about accessing with Enum objects, not values
    # TODO Needs to use DataEntryId.
    # Gets the most recent value specified by the sensor_id given
    def last_value_by_device(self, device: DeviceType, sensor_id):
        """

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

    # TODO make incoming converter from enum to const str (if key or val is enum (or object?))
    # Data saving function that creates csv
    def save(self, csvpath):
        """

        :param csvpath:
        :type csvpath:
        :return:
        :rtype:
        """
        with self.data_lock:
            if len(self.timeset) <= 0:
                return

            keys = list(self.existing_entry_keys)

            data = np.empty((len(keys), len(self.timeset) + 1), dtype=object)
            times = list(self.timeset.keys())
            times.sort(reverse=False)
            for ix, iy in np.ndindex(data.shape):
                # Make the first row a list of sensor names
                if iy == 0:
                    name = DataEntryIds(keys[ix].data_id).name if type(keys[ix].data_id) is int else str(keys[ix].data_id)
                    device = self.device_manager.get_device_type(keys[ix].full_address)

                    data[ix, iy] = name + '_' + device.name if device else \
                        f"{keys[ix].full_address.connection_name}_{keys[ix].full_address.device_address}"
                else:
                    if keys[ix].data_id == DataEntryIds.TIME.value:
                        data[ix, iy] = times[iy - 1]
                    else:
                        if keys[ix] in self.timeset[times[iy - 1]]:
                            data[ix, iy] = self.timeset[times[iy - 1]][keys[ix]]
                        else:
                            data[ix, iy] = ""

        np.savetxt(csvpath, np.transpose(data), delimiter=',',
                   fmt="%s")  # Can free up the lock while we save since were no longer accessing the original data

    # Add a new callback for its associated ID
    def addNewCallback(self, device: DeviceType, data_id, callbackFn):
        """

        :param data_id:
        :type data_id:
        :param callbackFn:
        :type callbackFn:
        """
        with self.callback_lock:
            key = CallBackKey(device, data_id)
            if key not in self.callbacks.keys():
                self.callbacks[key] = [callbackFn]
            else:
                self.callbacks[key].append(callbackFn)

    def _notifyCallbacksOfId(self, key: CallBackKey):
        """

        :param data_id:
        :type data_id:
        """
        with self.callback_lock:
            if key in self.callbacks.keys():
                for fn in self.callbacks[key]:
                    fn()

    def _notifyAllCallbacks(self):
        """

        """
        with self.callback_lock:
            for key in self.callbacks.keys():
                self._notifyCallbacksOfId(key)
