"""This file is meant to contain all the commonly used functions and constants"""

import os
import sys

# Path to executable
if getattr(sys, 'frozen', False):
    LOCAL = os.path.dirname(sys.executable)
elif __file__:
    LOCAL = os.path.dirname(__file__)
