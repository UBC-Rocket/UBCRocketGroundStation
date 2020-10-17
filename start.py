import sys

from com_window.main import comWindow
from PyQt5 import QtWidgets

from util.detail import init_logger, LOGGER

if __name__ == "__main__":
    init_logger()

    app = QtWidgets.QApplication(sys.argv)
    window = comWindow()
    window.show()
    sys.exit(app.exec_())
