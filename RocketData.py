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
    "Acceleration X": 'X'.encode('ascii'),
    "Acceleration Y": 'Y'.encode('ascii'),
    "Acceleration Z": 'Z'.encode('ascii'),
    "Pressure": 'P'.encode('ascii'),
    "Barometer Temperature": '~'.encode('ascii'),
    "Temperature": 'T'.encode('ascii'),
    "Yaw": '@'.encode('ascii'),
    "Roll": '#'.encode('ascii'),
    "Pitch": '$'.encode('ascii'),
    "Latitude": 'L'.encode('ascii'),
    "Longitude": 'l'.encode('ascii'),
    "GPS Altitude": 'A'.encode('ascii'),
    "Calculated Altitude": 'a'.encode('ascii'),
    "State": 's'.encode('ascii'),
    "Voltage": 'b'.encode('ascii'),
    "Ground Altitude": 'g'.encode('ascii'),
    "Time": 't'.encode('ascii')
}

chartoname = {}
for x in nametochar:
    chartoname[nametochar[x]] = x

orderednames = list(nametochar.keys())
orderednames.sort()

class RocketData:
    def __init__(self):
        self.timeset = {}
        self.lasttime = 0

    def addpoint(self, bytes):
        if bytes[0] == nametochar["Time"][0]:
            self.lasttime = self.fivetofloat(bytes)
        else:
            if self.lasttime not in self.timeset:
                self.timeset[self.lasttime] = {}

            (self.timeset[self.lasttime])[chr(bytes[0])] = self.fivetofloat(bytes)

    def lastvalue(self, name):
        times = list(self.timeset.keys())
        times.sort(reverse=True)
        for i in range(len(times)):
            if chr(nametochar[name][0]) in self.timeset[times[i]]:
                return self.timeset[times[i]][chr(nametochar[name][0])]
        return None

    def fivetofloat(self, bytes):
        # turns d into a float from decimal representation of 4 sepreate bytes in a list
        data = bytes[1:5]
        #data = data[::-1]#flips bytes
        b = struct.pack('4B', *data)
        # should be in little endian format from the teensy?
        c = struct.unpack('<f', b)
        return c[0]

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
