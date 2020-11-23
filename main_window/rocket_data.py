import os
import threading
from typing import Dict, Union
from collections import namedtuple

import numpy as np

from . import subpacket_ids
from util.detail import LOGS_DIR, SESSION_ID, LOGGER
from util.event_stats import Event
from .subpacket_ids import SubpacketEnum
from .device_manager import DeviceType

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

typemap = {  # TODO Review legacy data format
    's': "state",
    't': "int"
}

statemap = {  # TODO Review legacy data format. Not deleted due to need to confer with frontend
    0: "STANDBY",
    1: "ARMED",
    2: "ASCENT",
    3: "MACH_LOCK",
    4: "PRESSURE_DELAY",
    5: "INITIAL_DESCENT",
    6: "FINAL_DESCENT",
    7: "LANDED",
    8: "WINTER_CONTINGENCY"
}

DataEntryKey = namedtuple('DataEntry', ['device', 'data_id'])

AUTOSAVE_INTERVAL_S = 10

class RocketData:
    def __init__(self) -> None:
        """
        Timeset is dictionary of all of the time points mapped to a dictionary of id -> value.
        """

        self.lock = threading.RLock()  # acquire lock ASAP since self.lock needs to be defined when autosave starts
        self.timeset: Dict[int, Dict[DataEntryKey, Union[int, float]]] = {}
        self.lasttime = 0  # TODO REVIEW/CHANGE THIS, once all subpackets have their own timestamp.
        self.highest_altitude = 0
        self.sessionName = os.path.join(LOGS_DIR, "autosave_" + SESSION_ID + ".csv")
        self.existing_entry_keys = set() # Set of entry keys that have actually been recorded. Used for creating csv header

        self.callbacks = {}

        self.as_cv = threading.Condition()  # Condition variable for autosave (as)
        self._as_is_shutting_down = False  # Lock in cv is used to protect this

        self.autosaveThread = threading.Thread(target=self.timer, daemon=True, name="AutosaveThread")
        self.autosaveThread.start()

    def timer(self):
        """

        """
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

    # adding a bundle of data points and trigger callbacks according to id
    # Current implementation: adds to time given, otherwise will add to the last time received?
    # NOTE how this works without a new time eg if single sensor temperature comes in 3 times in a row, the first two are overwritten
    # |_> https://trello.com/c/KE0zJ7er/170-implement-ensure-spec-where-all-subpackets-will-have-timestamps
    def addBundle(self, device: DeviceType, incoming_data):
        """

        :param incoming_data:
        :type incoming_data:
        """
        with self.lock:
            # if there's a time, set this to the most recent time val
            if SubpacketEnum.TIME.value in incoming_data.keys():
                self.lasttime = incoming_data[SubpacketEnum.TIME.value]
            # if the timeset then setup a respective dict for the data
            if self.lasttime not in self.timeset.keys():
                self.timeset[self.lasttime] = {}

            # write the data and call the respective callbacks
            for data_id in incoming_data.keys():
                key = DataEntryKey(device, data_id)
                self.existing_entry_keys.add(key)
                self.timeset[self.lasttime][key] = incoming_data[data_id]

        # Notify after all data has been updated
        # Also, do so outside lock to prevent mutex contention with notification listeners
        for data_id in incoming_data.keys():
            key = DataEntryKey(device, data_id)
            self._notifyCallbacksOfId(key)

        BUNDLE_ADDED_EVENT.increment()

    # Gets the most recent value specified by the sensor_id given
    def last_value_by_device(self, device: DeviceType, sensor_id):
        """

        :param sensor_id:
        :type sensor_id:
        :return:
        :rtype:
        """
        with self.lock:
            times = list(self.timeset.keys())
            times.sort(reverse=True) # TODO : Should probably use OrderedDict to improve performance

            data_entry_key = DataEntryKey(device, sensor_id)
            for i in range(len(times)):
                if data_entry_key in self.timeset[times[i]]:
                    return self.timeset[times[i]][data_entry_key]
            return None

    # Data saving function that creates csv
    def save(self, csvpath):
        """

        :param csvpath:
        :type csvpath:
        :return:
        :rtype:
        """
        with self.lock:
            if len(self.timeset) <= 0:
                return

            keys = list(self.existing_entry_keys)

            data = np.empty((len(keys), len(self.timeset) + 1), dtype=object)
            times = list(self.timeset.keys())
            times.sort(reverse=False)
            for ix, iy in np.ndindex(data.shape):
                # Make the first row a list of sensor names
                if iy == 0:
                    name = SubpacketEnum(keys[ix].data_id).name if type(keys[ix].data_id) is int else str(keys[ix].data_id)
                    data[ix, iy] = name + '_' + keys[ix].device.name
                else:
                    if keys[ix].data_id == SubpacketEnum.TIME.value:
                        data[ix, iy] = times[iy - 1]
                    else:
                        if keys[ix] in self.timeset[times[iy - 1]]:
                            data[ix, iy] = self.timeset[times[iy - 1]][keys[ix]]
                        else:
                            data[ix, iy] = ""

        np.savetxt(csvpath, np.transpose(data), delimiter=',',
                   fmt="%s")  # Can free up the lock while we save since were no longer accessing the original data

    # TODO possibly make into own object/file
    # Add a new callback for its associated ID
    def addNewCallback(self, device: DeviceType, data_id, callbackFn):
        """

        :param data_id:
        :type data_id:
        :param callbackFn:
        :type callbackFn:
        """
        key = DataEntryKey(device, data_id)
        if key not in self.callbacks.keys():
            self.callbacks[key] = [callbackFn]
        else:
            self.callbacks[key].append(callbackFn)

    def _notifyCallbacksOfId(self, key: DataEntryKey):
        """

        :param data_id:
        :type data_id:
        """
        if key in self.callbacks.keys():
            for fn in self.callbacks[key]:
                fn()

    def _notifyAllCallbacks(self):
        """

        """
        for key in self.callbacks.keys():
            self._notifyCallbacksOfId(key)
