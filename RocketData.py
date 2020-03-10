import os
import struct
import sys

import numpy as np
import time

if getattr(sys, 'frozen', False):
    local = os.path.dirname(sys.executable)
elif __file__:
    local = os.path.dirname(__file__)

nametochar = {
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
    "Calculated Altitude": b'a',
    "State": b's',
    "Voltage": b'b',
    "Ground Altitude": b'g',
    "Time": b't'
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

class RocketData:
    def __init__(self):
        self.timeset = {}
        self.lasttime = 0
        self.highest_altitude = 0

    def addpoint(self, bytes):
        if bytes[0] == nametochar["Time"][0]:
            self.lasttime = fivtoval(bytes)
        else:
            if self.lasttime not in self.timeset:
                self.timeset[self.lasttime] = {}

            (self.timeset[self.lasttime])[chr(bytes[0])] = fivtoval(bytes)

        if bytes[0] == nametochar["Calculated Altitude"][0]:
            alt = fivtoval(bytes)
            if alt > self.highest_altitude:
                self.highest_altitude = alt

    def lastvalue(self, name):
        times = list(self.timeset.keys())
        times.sort(reverse=True)
        for i in range(len(times)):
            if chr(nametochar[name][0]) in self.timeset[times[i]]:
                return self.timeset[times[i]][chr(nametochar[name][0])]
        return None

    def save(self):
        if len(self.timeset) <= 0:
            return

        csvpath = os.path.join(local, str(int(time.time()))+".csv")

        data = np.empty((len(orderednames), len(self.timeset)+1), dtype=object)
        times = list(self.timeset.keys())
        times.sort(reverse=False)
        for ix, iy in np.ndindex(data.shape):
            if iy == 0:
                data[ix,iy] = orderednames[ix]
            else:
                if orderednames[ix] == "Time":
                    data[ix, iy] = times[iy-1]
                else:
                    char = chr(nametochar[orderednames[ix]][0])
                    if char in self.timeset[times[iy-1]]:
                        data[ix, iy] = self.timeset[times[iy-1]][char]
                    else:
                        data[ix, iy] = ""

        np.savetxt(csvpath, np.transpose(data), delimiter=',', fmt="%s")

def bytelist(bytes):
    return list(map(lambda x: x[0], bytes))

def tostate(bytes):
    return statemap[toint(bytes)]


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

def fivtoval(bytes):    # TODO Review this function
    data = bytes[1:5]
    val = 0

    try:
        if chr(bytes[0]) in typemap:
            datatype = typemap[chr(bytes[0])]

            if datatype == "int":
                return toint(data)
            elif datatype == "state":
                return tostate(data)

        return fourtofloat(data)

    except:
        return -1