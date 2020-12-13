"""This file is meant to contain all the commonly used functions and constants"""

import os
import sys
import time
import logging
from copy import copy

from PyQt5.QtCore import pyqtSignal, QObject

# Path to executable
if getattr(sys, 'frozen', False):
    # Running in pyinstaller
    IS_PYINSTALLER = True
    LOCAL = os.path.dirname(sys.executable)
    BUNDLED_DATA = sys._MEIPASS # Files that we bundle with the final file (e.g .ui files, images, etc.)
elif __file__:
    # Running normally
    IS_PYINSTALLER = False
    LOCAL = os.path.dirname(__file__)
    assert os.path.basename(LOCAL) == "util"
    LOCAL = os.path.abspath(os.path.join(LOCAL, os.pardir))
    BUNDLED_DATA = LOCAL

LOGS_DIR = os.path.join(LOCAL, "logs")

if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)

SESSION_ID = str(int(time.time()))

# DEBUG      Informational log, useful only to developers
# INFO       Informational log, useful to users
# WARNING    Warning of unusual events
# ERROR      Warning that something broke
# CRITICAL   Impending crash, application terminating event.
LOGGER = logging.getLogger("main")

LOGGER.setLevel(logging.DEBUG)

_logger_format = logging.Formatter("[%(asctime)s] (%(levelname)s) %(filename)s:%(funcName)s: %(message)s")

_file_handler = logging.FileHandler(os.path.join(LOGS_DIR, "debuglog_" + SESSION_ID + ".txt"))
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_logger_format)

_stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setLevel(logging.DEBUG)
_stdout_handler.setFormatter(_logger_format)

LOGGER.addHandler(_file_handler)
LOGGER.addHandler(_stdout_handler)

LOGGER.info(f"Starting session ID: {SESSION_ID}")

class qtSignalLogHandler(logging.Handler, QObject):
    """
    Logging handler that passes logs to a Qt signal

    Required for printing logs in a UI as LOGGER is multithreaded and safely accessing the UI from other threads
    requires the use of a signal
    """

    qt_signal = pyqtSignal(str)

    def __init__(self, exception_traces=True):
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.exception_traces = exception_traces

    def emit(self, record):
        if not self.exception_traces:
            # Shallow copy so that we dont modify record for other handlers. Inspired by:
            # https://stackoverflow.com/questions/54605699/python-logging-disable-stack-trace
            record = copy(record)
            record.exc_info = None
            record.exc_text = None

        log_entry = self.format(record)
        self.qt_signal.emit(log_entry)


EXECUTABLE_FILE_EXTENSION = {
    'linux': '',
    'win32': '.exe',
    'darwin': ''
}[sys.platform]

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
