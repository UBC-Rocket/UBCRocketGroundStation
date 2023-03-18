"""
Module includes AccelWidget class
"""
from PyQt5 import QtWidgets
from main_window.mplwidget import MplWidget


class AccelWidget(MplWidget):
    """
    Widget with checkboxes for plotting acceleration graphs
    """
    def __init__(self):
        MplWidget.__init__(self)
        self.accel_checkboxes = [QtWidgets.QCheckBox("Acceleration X"),
                                 QtWidgets.QCheckBox("Acceleration Y"),
                                 QtWidgets.QCheckBox("Acceleration Z")]
        self.showing_checkboxes = False

        for checkbox in self.accel_checkboxes:
            self.vbl.addWidget(checkbox)
        self.hide_checkboxes()

    def hide_checkboxes(self):
        """
        Hide checkboxes in main window when not viewing acceleration data
        """
        for checkbox in self.accel_checkboxes:
            checkbox.setVisible(False)
        self.showing_checkboxes = False

    def show_checkboxes(self):
        """
        Show checkboxes in main window when viewing acceleration data
        """
        for checkbox in self.accel_checkboxes:
            checkbox.setVisible(True)
        self.showing_checkboxes = True
