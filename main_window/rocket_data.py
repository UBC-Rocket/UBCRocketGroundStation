import os
import sys
import threading
import time
from typing import Dict, Union

import numpy as np

from . import subpacket_ids
from detail import LOCAL
from .subpacket_ids import SubpacketEnum

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
    's':"state",
    't':"int"
}

statemap = {  # TODO Review legacy data format. Not deleted due to need to confer with frontend
 0:"STANDBY",
 1:"ARMED",
 2:"ASCENT",
 3:"MACH_LOCK",
 4:"PRESSURE_DELAY",
 5:"INITIAL_DESCENT",
 6:"FINAL_DESCENT",
 7:"LANDED",
 8:"WINTER_CONTINGENCY"
}

# Supposedly a dictionary of all of the time points mapped to a dictionary of sensor id to value.
# self.timeset:    dictionary designed to hold time - dictionary {sensor id - value} pairs.
        # essentially  self.data: Dict[int, Dict[str, Union[int, float]]] = {}

class RocketData:
    def __init__(self) -> None:
        """

        """

        if not os.path.exists(os.path.join(LOCAL, "logs")):
            os.mkdir(os.path.join(LOCAL, "logs"))

        self.lock = threading.RLock()  # acquire lock ASAP since self.lock needs to be defined when autosave starts
        self.timeset: Dict[int, Dict[str, Union[int, float]]] = {}
        self.lasttime = 0  # TODO REVIEW/CHANGE THIS, once all subpackets have their own timestamp.
        self.highest_altitude = 0
        self.sessionName = os.path.join(LOCAL, "logs", "autosave_" + str(int(time.time())) + ".csv")
        self.autosaveThread = threading.Thread(target=self.timer, daemon=True)
        self.autosaveThread.start()

        #  Create Dict of lists, with ids as keys
        self.callbacks = {k: [] for k in subpacket_ids.get_list_of_IDs()}

    def timer(self):
        """

        """
        while True:
            try:
                self.save(self.sessionName)
                print("Auto-Save successful.")
            except Exception as e:
                print(e)
                print("FAILED TO SAVE. Something went wrong")
            time.sleep(10)

    # adding a bundle of data points and trigger callbacks according to id
    # Current implementation: adds to time given, otherwise will add to the last time received?
    # NOTE how this works without a new time eg if single sensor temperature comes in 3 times in a row, the first two are overwritten
    # |_> https://trello.com/c/KE0zJ7er/170-implement-ensure-spec-where-all-subpackets-will-have-timestamps
    def addBundle(self, incoming_data):
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
                self.timeset[self.lasttime][data_id] = incoming_data[data_id]
        tempvar = 1 # for debug

        # Notify after all data has been updated
        # Also, do so outside lock to prevent mutex contention with notification listeners
        for data_id in incoming_data.keys():
            self._notifyCallbacksOfId(data_id)

    # TODO REMOVE this function once data types refactored
    # # In the previous version this is supposed to save very specifically formatted incoming data into RocketData
    # def addpoint(self, bytes):
    #     with self.lock:
    #         if bytes[0] == nametochar["Time"][0]:
    #             self.lasttime = fivtoval(bytes)
    #         else:
    #             if self.lasttime not in self.timeset:
    #                 self.timeset[self.lasttime] = {}
    #
    #             (self.timeset[self.lasttime])[chr(bytes[0])] = fivtoval(bytes)
    #
    #         if bytes[0] == nametochar["Calculated Altitude"][0]:
    #             alt = fivtoval(bytes)
    #             if alt > self.highest_altitude:
    #                 self.highest_altitude = alt

    # Gets the most recent value specified by the sensor_id given
    def lastvalue(self, sensor_id):
        """

        :param sensor_id:
        :type sensor_id:
        :return:
        :rtype:
        """
        with self.lock:
            times = list(self.timeset.keys())
            times.sort(reverse=True)
            for i in range(len(times)):
                if sensor_id in self.timeset[times[i]]:
                    return self.timeset[times[i]][sensor_id]
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

            data = np.empty((len(subpacket_ids.get_list_of_sensor_IDs()), len(self.timeset) + 1), dtype=object)
            times = list(self.timeset.keys())
            times.sort(reverse=False)
            for ix, iy in np.ndindex(data.shape):
                # Make the first row a list of sensor names
                if iy == 0:
                    data[ix, iy] = subpacket_ids.get_list_of_sensor_names()[ix]
                else:
                    if subpacket_ids.get_list_of_sensor_names()[ix] == SubpacketEnum.TIME.name:
                        data[ix, iy] = times[iy - 1]
                    else:
                        if subpacket_ids.get_list_of_sensor_IDs()[ix] in self.timeset[times[iy - 1]]:
                            data[ix, iy] = self.timeset[times[iy - 1]][subpacket_ids.get_list_of_sensor_IDs()[ix]]
                        else:
                            data[ix, iy] = ""

        np.savetxt(csvpath, np.transpose(data), delimiter=',',
                   fmt="%s")  # Can free up the lock while we save since were no longer accessing the original data

    # TODO possibly make into own object/file
    # Add a new callback for its associated ID
    def addNewCallback(self, data_id, callbackFn):
        """

        :param data_id:
        :type data_id:
        :param callbackFn:
        :type callbackFn:
        """
        self.callbacks[data_id].append(callbackFn)

    def _notifyCallbacksOfId(self, data_id):
        """

        :param data_id:
        :type data_id:
        """
        if data_id in self.callbacks.keys():
            for fn in self.callbacks[data_id]:
                fn()

    def _notifyAllCallbacks(self):
        """

        """
        for data_id in self.callbacks.keys():
            self._notifyCallbacksOfId(data_id)
