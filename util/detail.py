"""This file is meant to contain all the commonly used functions and constants"""

import os
import sys

# Path to executable
if getattr(sys, 'frozen', False):
    LOCAL = os.path.dirname(sys.executable)
elif __file__:
    LOCAL = os.path.dirname(__file__)

assert os.path.basename(LOCAL) == "util"

LOCAL = os.path.abspath(os.path.join(LOCAL, os.pardir))

LOGS_DIR = os.path.join(LOCAL, "logs")

if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)

# Helper class. python way of doing ++ (unlimited incrementing)
class Count:
    def __init__(self, start=0, interval=1):
        """

        :param bigEndianInts:
        :type bigEndianInts:
        :param bigEndianFloats:
        :type bigEndianFloats:
        """
        self.interval = interval
        self.num = start

    def __iter__(self):
        return self

    def curr(self):
        return self.num

    # increments and returns the new value
    def next(self, interval=0):
        if interval == 0:
            self.num += self.interval
        else:
            self.num += interval

        return self.num

    # returns the current value then increments
    def currAndInc(self, interval=9):
        num = self.num
        if interval == 0:
            self.num += self.interval
        else:
            self.num += interval

        return num
