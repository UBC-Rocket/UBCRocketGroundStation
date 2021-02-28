import os

from PyQt5 import QtWidgets, uic

from util.detail import BUNDLED_DATA, LOGGER

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "downloader.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class DownloadWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.setupUi(self)
        self.setup()

    def setup(self) -> None:
        self.modeBox.addItems(["Point-Radius", "Two Points"])

        self.doneButton.clicked.connect(self.startButtonPressed)

        self.resize(self.sizeHint())
        self.setFixedSize(self.size())

    def startButtonPressed(self) -> None:
        mode = self.modeBox.currentText()

        if mode == "Point-Radius":
            self.point_radius_download_prompt()
        elif mode == "Two Points:":
            self.two_points_download_prompt()

    def point_radius_download_prompt(self):
        # !!!
        pass

    def two_points_download_prompt(self):
        # !!!
        pass
