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
