from PyQt5.QtWidgets import QCheckBox
from main_window.mplwidget import MplWidget


class AccelWidget(MplWidget):
    """
    Widget with checkboxes for plotting acceleration graphs
    """
    def __init__(self):
        MplWidget.__init__(self)  # Inherit from MplWidget
        self.accel_checkboxes = [QCheckBox("Acceleration X (Red)"),
                                 QCheckBox("Acceleration Y (Blue)"),
                                 QCheckBox("Acceleration Z (Green)")]
        self.showing_checkboxes = False

        for checkbox in self.accel_checkboxes:
            self.vbl.addWidget(checkbox)
        self.hide_checkboxes()

    def hide_checkboxes(self):
        for checkbox in self.accel_checkboxes:
            checkbox.setVisible(False)
        self.showing_checkboxes = False

    def show_checkboxes(self):
        for checkbox in self.accel_checkboxes:
            checkbox.setVisible(True)
        self.showing_checkboxes = True
