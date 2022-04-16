import math
import os
from typing import Dict

from PyQt5 import QtCore, QtGui, QtWidgets, uic

from connections.connection import Connection
from util.detail import LOCAL, BUNDLED_DATA

from profiles.rocket_profile import RocketProfile

from main_window.main_app import MainApp

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "wb_app.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WbApp(MainApp, Ui_MainWindow):

    def __init__(self, connections: Dict[str, Connection], rocket_profile: RocketProfile) -> None:
        """

        :param connection:
        :type connection: Connection
        :param rocket_profile:
        :type rocket_profile: RocketProfile
        """
        super().__init__(connections, rocket_profile)  # Must call base

        # Set up UI stuff using base class here. E.g.:
        # self.armingButton.clicked.connect(self.arming_button_pressed)

    def setup_buttons(self):
        """Create all of the buttons for the loaded rocket profile."""

        grid_width = math.ceil(math.sqrt(len(self.rocket_profile.buttons)))

        # Trying to replicate PyQt's generated code from a .ui file as closely as possible. This is why setattr is
        # being used to keep all of the buttons as named attributes of MainApp and not elements of a list.
        row = 0
        col = 0
        for button in self.rocket_profile.buttons:
            qt_button = QtWidgets.QPushButton(self.centralwidget)
            setattr(self, button + "Button", qt_button)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            sizePolicy.setHeightForWidth(getattr(self, button + "Button").sizePolicy().hasHeightForWidth())
            qt_button.setSizePolicy(sizePolicy)
            font = QtGui.QFont()
            font.setPointSize(16)
            font.setKerning(True)
            qt_button.setFont(font)
            qt_button.setObjectName(f"{button}Button")
            self.commandButtonGrid.addWidget(qt_button, row, col, 1, 1)
            if col + 1 < grid_width:
                col += 1
            else:
                col = 0
                row += 1
        # A .py file created from a .ui file will have the labels all defined at the end, for some reason. Two for loops
        # are being used to be consistent with the PyQt5 conventions.
        for button in self.rocket_profile.buttons:
            getattr(self, button + "Button").setText(QtCore.QCoreApplication.translate('MainWindow', button))

        def gen_send_command(cmd: str) -> Callable[[], None]:
            """Creates a function that sends the given command to the console."""

            def send() -> None:
                self.send_command(cmd)

            return send

        # Connecting to a more traditional lambda expression would not work in this for loop. It would cause all of the
        # buttons to map to the last command in the list, hence the workaround with the higher order function.
        for button, command in self.rocket_profile.buttons.items():
            getattr(self, button + "Button").clicked.connect(gen_send_command(command))



    def arming_button_pressed(self):
        self.send_command('ARM')

    def receive_data(self) -> None:
        """
        This is called when new data is available to be displayed.
        :return:
        :rtype:
        """

        # Handle new data here. New data is put retrieved from rocket_data. E.g.:
        # self.pressureLabel.setText(self.rocket_data.last_value_by_device(DataEntryIds.PRESSURE))

        pass

    ''' # Optional implementation
    def shutdown(self):
        """
        This is called when the app is being requested to shut down
        :return:
        :rtype:
        """
        
        # Handle shutdown stuff here
        
        super().shutdown() # Must always call base
    '''
