import os
import struct
import sys
from typing import Dict, Union, Set

import numpy as np
import time

from SubpacketIDs import SubpacketEnum
import SubpacketIDs

if getattr(sys, 'frozen', False):
    local = os.path.dirname(sys.executable)
elif __file__:
    local = os.path.dirname(__file__)

# Source of ```ORDERED``` sensor types. DO NOT MODIFY WITHOUT CONSIDERING EFFECTS ON ALL DATA PARSING AND SAVING.
nametochar : Dict[str, bytes] = {
    "Acceleration X": b'X',
    "Acceleration Y": b'Y',
    "Acceleration Z": b'Z',
    "Pressure": b'P',
    "Barometer Temperature": b'~',
    "Temperature": b'T',
    "Yaw": b'@',
    "Roll": b'#',
    "Pitch": b'$',
    "Latitude": b'L',
    "Longitude": b'l',
    "GPS Altitude": b'A',
    "Calculated Altitude": b'a', # barometer altitude TODO Ensure that this is calculated and not just the pressure
    "State": b's',
    "Voltage": b'b',
    "Ground Altitude": b'g',
    "Time": b't',
    "Orientation 1": b'o', # TODO review this
    "Orientation 2": b'p',
    "Orientation 3": b'q',
    # TODO 4th orientation value calculated since it is a quaternion?
}

chartoname = {}
for x in nametochar:
    chartoname[nametochar[x]] = x

orderednames = list(nametochar.keys())
orderednames.sort()

typemap = {
    's':"state",
    't':"int"
}

statemap = {
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
    # Current implementation

class RocketData:
    def __init__(self):
        # dictionary designed to hold time - dictionary {sensor id - value} pairs. TODO Is time a float or int?
                # essentially  self.data: Dict[int, Dict[str, Union[int, float]]] = {}
        self.timeset: Dict[int, Dict[str, Union[int, float]]] = {}
        self.lasttime = 0
        self.highest_altitude = 0

    # TODO Review how this works eg if single sensor temperature comes in 3 times in a row, the first two are overwritten
    # adding a bundle of data points
    # Current implementation: adds to time given, otherwise will add to the last time recieved?
    def addBundle(self, incoming_data):
        if SubpacketEnum.TIME.value in incoming_data.keys():
            self.lasttime = incoming_data[SubpacketEnum.TIME.value]
        if self.lasttime not in self.timeset.keys():
            self.timeset[self.lasttime] = {}

        for id in incoming_data.keys():
            self.timeset[self.lasttime][id] = incoming_data[id]

    # # In the previous version this is supposed to save very specifically formatted incoming data into RocketData
    # def addpoint(self, bytes):
    #     if bytes[0] == nametochar["Time"][0]:
    #         self.lasttime = fivtoval(bytes)
    #     else:
    #         if self.lasttime not in self.timeset:
    #             self.timeset[self.lasttime] = {}
    #
    #         (self.timeset[self.lasttime])[chr(bytes[0])] = fivtoval(bytes)
    #
    #     if bytes[0] == nametochar["Calculated Altitude"][0]:
    #         alt = fivtoval(bytes)
    #         if alt > self.highest_altitude:
    #             self.highest_altitude = alt

    # Gets the most recent value specified by the sensor_id given
    def lastvalue(self, sensor_id):
        times = list(self.timeset.keys())
        times.sort(reverse=True)
        for i in range(len(times)):
            if sensor_id in self.timeset[times[i]]:
                return self.timeset[times[i]][sensor_id]
        return None

    def save(self):
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

def bytelist(bytes):
    return list(map(lambda x: x[0], bytes))

# def tostate(bytes):
#     return statemap[toint(bytes)]


def toint(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=False)  #TODO discuss this byteorder change

def fourtofloat(bytes):
    data = bytes
    # data = data[::-1]#flips bytes
    b = struct.pack('4B', *data)
    # should be in little endian format from the teensy?  #TODO discuss this byteorder
    c = struct.unpack('<f', b)
    return c[0]

def fourtoint(bytes):
    data = bytes
    # data = data[::-1]#flips bytes
    b = struct.pack('4B', *data)
    # big endian  #TODO discuss this byteorder
    c = struct.unpack('>I', b)
    return c[0]

# def fivtoval(bytes):    # TODO Review this function
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