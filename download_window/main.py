import os

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox

from main_window.competition.mapping.mapbox_utils import advance_download_point_radius, advance_download_two_points
from util.detail import BUNDLED_DATA, LOGGER


qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "downloader.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


MODES = {
    #Input type: [lat1, long1, radius, lat2, long2]
    "Point-Radius": [True, True, True, False, False],
    "Two Points": [True, True, False, True, True],
}


class DownloadWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.mode = None
        self.setupUi(self)
        self.setup()

    def setup(self) -> None:
        self.modeBox.addItems(["Point-Radius", "Two Points"])
        self.modeBox.currentTextChanged.connect(self.modeChanged)

        self.doneButton.clicked.connect(self.startButtonPressed)
        self.modeChanged()

        self.resize(self.sizeHint())
        self.setFixedSize(self.size())

    def modeChanged(self) -> None:
        text = self.modeBox.currentText()
        requirements = MODES[text]

        self.lat1.setEnabled(requirements[0])
        self.long1.setEnabled(requirements[1])
        self.radius.setEnabled(requirements[2])
        self.lat2.setEnabled(requirements[3])
        self.long2.setEnabled(requirements[4])

        if text == "Point-Radius":
            self.radius.setStyleSheet("""QLineEdit { background-color: white;}""")
            self.lat2.setStyleSheet("""QLineEdit { background-color: gray;}""")
            self.long2.setStyleSheet("""QLineEdit { background-color: gray;}""")

        else:
            self.radius.setStyleSheet("""QLineEdit { background-color: gray;}""")
            self.lat2.setStyleSheet("""QLineEdit { background-color: white;}""")
            self.long2.setStyleSheet("""QLineEdit { background-color: white;}""")

    def startButtonPressed(self) -> None:
        self.mode = self.modeBox.currentText()

        if self.mode == "Point-Radius":
            self.point_radius_download_prompt()
        elif self.mode == "Two Points":
            self.two_points_download_prompt()


    def point_radius_download_prompt(self):
        valid = self.check_input(self.lat1.text(), self.long1.text(), self.radius.text(), "0", "0")

        if valid:
            # TODO: change color of disabled lineedit input
            #lat, long, radius, zoom
            advance_download_point_radius(float(self.lat1.text()), float(self.long1.text()),
                                          float(self.radius.text()), 17) #TODO: change zoom
            LOGGER.debug("Successfully downloaded point radius map tiles")
            self.close()
        else:
            msg = QMessageBox()
            msg.setText("Invalid values entered")
            msg.exec_()


    def two_points_download_prompt(self):
        valid = self.check_input(self.lat1.text(), self.long1.text(), "1", self.lat2.text(), self.long2.text())

        if valid:
            advance_download_two_points(float(self.lat1.text()), float(self.long1.text()),
                                          float(self.lat2.text()), float(self.long2.text()), 17)
            LOGGER.debug("Successfully downloaded two point map tiles")
            self.close()
        else:
            msg = QMessageBox()
            msg.setText("Invalid values entered")
            msg.exec_()


    def check_input(self, lat1, long1, radius, lat2, long2):

        try:
            lat1 = float(lat1)
            long1 = float(long1)
            radius = float(radius)
            lat2 = float(lat2)
            long2 = float(long2)

            if lat1 > 90 or lat1 < -90:
                return False
            if long1 > 180 or long1 < -180:
                return False
            if radius <= 0:
                return False
            if lat2 > 90 or lat2 < -90:
                return False
            if long2 > 180 or long2 < -180:
                return False

            return True

        except:
            return False



