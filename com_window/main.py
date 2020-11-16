import os

import PyQt5
import serial.tools.list_ports
from PyQt5 import QtCore, QtWidgets, uic

from connections.debug.debug_connection_factory import DebugConnectionFactory
from connections.serial.serial_connection_factory import SerialConnectionFactory
from connections.sim.sim_connection_factory import SimConnectionFactory
from util.detail import BUNDLED_DATA, LOGGER
from profiles.rockets.co_pilot import CoPilotProfile
from profiles.rockets.tantalus import TantalusProfile
from profiles.rockets.whistler_blackcomb import WbProfile

if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "com_window.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class ComWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        """

        """
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.ConnectionFactories = {c.connection_name:c for c in [
            SerialConnectionFactory(),
            DebugConnectionFactory(),
            SimConnectionFactory(),
        ]}

        self.RocketProfiles = {p.rocket_name:p for p in [
            TantalusProfile(),
            CoPilotProfile(),
            WbProfile(),
        ]}

        self.chosen_connection = None
        self.chosen_rocket = None

        self.setupUi(self)
        self.setup()

    def setup(self) -> None:
        """

        """
        self.typeBox.currentTextChanged.connect(self.connectionChanged)
        self.typeBox.addItems(self.ConnectionFactories.keys())

        self.rocketBox.addItems(self.RocketProfiles.keys())

        self.doneButton.clicked.connect(self.doneButtonPressed)
        comlist = list(map(lambda x: x.device, serial.tools.list_ports.comports()))
        self.comBox.addItems(comlist)

    def doneButtonPressed(self) -> None:
        """

        """
        rocket = self.rocketBox.currentText()
        connection = self.typeBox.currentText()
        baud_rate = int(self.baudBox.currentText())
        com_port = self.comBox.currentText()

        LOGGER.debug(f"User has selected rocket={rocket}, connection={connection}, com_port={com_port}, baud_rate={baud_rate}")

        self.chosen_rocket = self.RocketProfiles[rocket]
        factory = self.ConnectionFactories[connection]
        self.chosen_connection = factory.construct(comPort=com_port, baudRate=baud_rate, rocket=self.chosen_rocket)
        self.close()

    def connectionChanged(self) -> None:
        """

        """
        text = self.typeBox.currentText()
        factory = self.ConnectionFactories[text]

        self.comBox.setEnabled(factory.requires_com_port)
        self.baudBox.setEnabled(factory.requires_baud_rate)
