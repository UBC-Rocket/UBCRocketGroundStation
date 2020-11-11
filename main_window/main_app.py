import os
import threading

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal

from connections.connection import Connection
from util.detail import LOGS_DIR, SESSION_ID, LOGGER
from profiles.rocket_profile import RocketProfile

from main_window.read_thread import ReadThread
from main_window.rocket_data import RocketData
from main_window.send_thread import SendThread

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


class MainApp(QtWidgets.QMainWindow):
    sig_send = pyqtSignal(str)

    def __init__(self, connection: Connection, rocket_profile: RocketProfile) -> None:
        """

        :param connection:
        :type connection: Connection
        :param rocket_profile:
        :type rocket_profile: RocketProfile
        """
        # Prints constructor arguments, leave at top of constructor
        LOGGER.debug(f"Starting MainApp with {locals()}")

        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        self.connection = connection
        self.rocket_profile = rocket_profile
        self.rocket_data = RocketData()

        # Init and connection of ReadThread
        self.ReadThread = ReadThread(self.connection, self.rocket_data)
        self.ReadThread.sig_received.connect(self.receive_data)
        self.ReadThread.sig_print.connect(self.print_to_ui)
        self.ReadThread.start()

        # Init and connection of SendThread
        self.SendThread = SendThread(self.connection)
        self.sig_send.connect(self.SendThread.queueMessage)
        self.SendThread.sig_print.connect(self.print_to_ui)
        self.SendThread.start()

    def closeEvent(self, event) -> None:
        """
        This is called when application is closing
        :param event:
        :type event:
        """
        self.shutdown()

    def shutdown(self):
        LOGGER.debug(f"MainApp shutting down")
        self.ReadThread.shutdown()
        self.SendThread.shutdown()
        self.rocket_data.shutdown()
        self.connection.shutdown()
        LOGGER.debug(f"All threads shut down, remaining threads: {threading.enumerate()}")

        LOGGER.info("Saving...")
        self.rocket_data.save(os.path.join(LOGS_DIR, "finalsave_" + SESSION_ID + ".csv"))
        LOGGER.info("Saved!")

    def receive_data(self) -> None:
        """
        This is called when new data is available to be displayed.
        :return:
        :rtype:
        """
        pass

    def send_command(self, command) -> None:
        """
        Call this to send a command
        :param command:
        :type command:
        """
        self.sig_send.emit(command)

    def print_to_ui(self, text) -> None:
        """
        This is called when a thread wants to show a message in the UI
        :param text:
        :type text:
        """
        LOGGER.info(text)
