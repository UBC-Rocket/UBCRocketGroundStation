import os
import struct
import sys
import threading
import numpy as np
import time
from typing import Dict, Union

from SubpacketIDs import SubpacketEnum
import SubpacketIDs

if getattr(sys, 'frozen', False):
    local = os.path.dirname(sys.executable)
elif __file__:
    local = os.path.dirname(__file__)

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
#
# typemap = {  # TODO Review legacy data format
#     's':"state",
#     't':"int"
# }
#
# statemap = {  # TODO Review legacy data format
#  0:"STANDBY",
#  1:"ARMED",
#  2:"ASCENT",
#  3:"MACH_LOCK",
#  4:"PRESSURE_DELAY",
#  5:"INITIAL_DESCENT",
#  6:"FINAL_DESCENT",
#  7:"LANDED",
#  8:"WINTER_CONTINGENCY"
# }

# Supposedly a dictionary of all of the time points mapped to a dictionary of sensor id to value.
# self.data:    dictionary designed to hold time - dictionary {sensor id - value} pairs.
        # essentially  self.data: Dict[int, Dict[str, Union[int, float]]] = {}

class RocketData:
    def __init__(self):
        self.lock = threading.Lock() # acquire lock ASAP since self.lock needs to be defined when autosave starts
        self.timeset: Dict[int, Dict[str, Union[int, float]]] = {}
        self.lasttime = 0   # TODO REVIEW/CHANGE THIS, once all subpackets have their own timestamp.
        self.highest_altitude = 0
        self.sessionName = str(int(time.time()))
        self.autosaveThread = threading.Thread(target=self.timer, daemon=True)
        self.autosaveThread.start()

    def timer(self):
        while True:
            try:
                self.save("")
                print("Auto-Save successful.")
            except Exception as e:
                print(e)
                print("FAILED TO SAVE. Something went wrong")
            time.sleep(10)

    # adding a bundle of data points
    # Current implementation: adds to time given, otherwise will add to the last time received?
    # NOTE how this works without a new time eg if single sensor temperature comes in 3 times in a row, the first two are overwritten
    def addBundle(self, incoming_data):
        with self.lock:
            if SubpacketEnum.TIME.value in incoming_data.keys():
                self.lasttime = incoming_data[SubpacketEnum.TIME.value]
            if self.lasttime not in self.timeset.keys():
                self.timeset[self.lasttime] = {}

            for id in incoming_data.keys():
                self.timeset[self.lasttime][id] = incoming_data[id]

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

    # TODO REVIEW/IMPROVE THIS, once all subpackets have their own timestamp.
    # Gets the most recent value specified by the sensor_id given
    def lastvalue(self, sensor_id):
        with self.lock:
            times = list(self.timeset.keys())
            times.sort(reverse=True)
            for i in range(len(times)):
                if sensor_id in self.timeset[times[i]]:
                    return self.timeset[times[i]][sensor_id]
            return None

    # Data saving function that creates csv
    def save(self, name):
        with self.lock:
            if len(self.timeset) <= 0:
                return

            csvpath = os.path.join(local, str(int(time.time()))+".csv")
            data = np.empty((len(SubpacketIDs.get_list_of_sensor_IDs()), len(self.timeset)+1), dtype=object)
            times = list(self.timeset.keys())
            times.sort(reverse=False)
            for ix, iy in np.ndindex(data.shape):
                # Make the first row a list of sensor names
                if iy == 0:
                    data[ix, iy] = SubpacketIDs.get_list_of_sensor_names()[ix]
                else:
                    if SubpacketIDs.get_list_of_sensor_names()[ix] == SubpacketEnum.TIME.name:
                        data[ix, iy] = times[iy - 1]
                    else:
                        if SubpacketIDs.get_list_of_sensor_IDs()[ix] in self.timeset[times[iy-1]]:
                            data[ix, iy] = self.timeset[times[iy-1]][SubpacketIDs.get_list_of_sensor_IDs()[ix]]
                        else:
                            data[ix, iy] = ""

            np.savetxt(csvpath, np.transpose(data), delimiter=',', fmt="%s")


# TODO REVIEW/REMOVE this section once data types refactored

def bytelist(bytes):
    return list(map(lambda x: x[0], bytes))

# def tostate(bytes):
#     return statemap[toint(bytes)]

def toint(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=False)

def fourtofloat(bytes):
    data = bytes
    # data = data[::-1]#flips bytes
    b = struct.pack('4B', *data)
    # should be in little endian format from the teensy?
    c = struct.unpack('<f', b)
    return c[0]

def fourtoint(bytes):
    data = bytes
    # data = data[::-1]#flips bytes
    b = struct.pack('4B', *data)
    # big endian
    c = struct.unpack('>I', b)
    return c[0]

# def fivtoval(bytes):    # TODO REMOVE this function once data types refactored
#     data = bytes[1:5]
#     val = 0
#
#     try:
#         if chr(bytes[0]) in typemap:
#             datatype = typemap[chr(bytes[0])]
#
#             if datatype == "int":
#                 return toint(data)
#             elif datatype == "state":
#                 return tostate(data)
#
#         return fourtofloat(data)
#
#     except:
#         return -1
