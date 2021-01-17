import os
from collections import namedtuple

import PyQt5
import serial.tools.list_ports
from PyQt5 import QtCore, QtWidgets, uic

from util.detail import BUNDLED_DATA, LOGGER
from profiles.rocket_profile_list import ROCKET_PROFILES

if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "com_window.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

ConnectionRequirements = namedtuple('ConnectionRequirements', ['com_port', 'baud_rate'])

CONNECTIONS = {
    'Serial': ConnectionRequirements(com_port=True, baud_rate=True),
    'Debug': ConnectionRequirements(com_port=False, baud_rate=False),
    'SIM': ConnectionRequirements(com_port=False, baud_rate=False),
}

class ComWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        """

        """
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.RocketProfiles = {p.rocket_name:p for p in ROCKET_PROFILES}

        self.chosen_connection = None
        self.chosen_rocket = None

        self.setupUi(self)
        self.setup()

    def setup(self) -> None:
        """

        """
        self.typeBox.currentTextChanged.connect(self.connectionChanged)
        self.typeBox.addItems(CONNECTIONS.keys())

        self.rocketBox.addItems(self.RocketProfiles.keys())

        self.doneButton.clicked.connect(self.doneButtonPressed)
        comlist = list(map(lambda x: x.device, serial.tools.list_ports.comports()))
        self.comBox.addItems(comlist)

        self.resize(self.sizeHint())
        self.setFixedSize(self.size())

    def doneButtonPressed(self) -> None:
        """

        """
        rocket = self.rocketBox.currentText()
        connection = self.typeBox.currentText()
        baud_rate = int(self.baudBox.currentText())
        com_port = self.comBox.currentText()

        LOGGER.debug(f"User has selected rocket={rocket}, connection={connection}, com_port={com_port}, baud_rate={baud_rate}")

        self.chosen_rocket = self.RocketProfiles[rocket]

        if connection == 'Serial':
            self.chosen_connection = self.chosen_rocket.construct_serial_connection(com_port, int(baud_rate))
        elif connection == 'Debug':
            self.chosen_connection = self.chosen_rocket.construct_debug_connection()
        elif connection == 'SIM':
            self.chosen_connection = self.chosen_rocket.construct_sim_connection()
        else:
            raise Exception("Unknown connection")

        self.close()

    def connectionChanged(self) -> None:
        """

        """
        text = self.typeBox.currentText()
        requirements = CONNECTIONS[text]

        self.comBox.setEnabled(requirements.com_port)
        self.baudBox.setEnabled(requirements.baud_rate)
