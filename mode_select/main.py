import os

import PyQt5
from PyQt5 import QtCore, QtWidgets, uic

from com_window.main import ComWindow
from download_window.main import DownloadWindow
from util.detail import BUNDLED_DATA, LOGGER

if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "mode_select.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

WINDOWS = {
    "COM Selection": ComWindow,
    "Tile Downloader": DownloadWindow
}


class ModeSelect(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.chosen_window = None

        self.setupUi(self)
        self.setup()

    def setup(self) -> None:
        self.windowBox.addItems(WINDOWS.keys())

        self.doneButton.clicked.connect(self.doneButtonPressed)

        self.resize(self.sizeHint())
        self.setFixedSize(self.size())

    def doneButtonPressed(self) -> None:
        window = self.windowBox.currentText()

        LOGGER.debug(f"User has selected {window}")

        # self.chosen_window = WINDOWS[window]
        self.chosen_window = window

        self.close()
