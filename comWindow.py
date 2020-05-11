import sys
import PyQt5
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import os
import start
import serial.tools.list_ports
from detail import *

from DebugConnectionFactory import DebugConnectionFactory
from SerialConnectionFactory import SerialConnectionFactory
from SimConnectionFactory import SimConnectionFactory

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(LOCAL, "comWindow.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class comWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.ConnectionFactories = {
            "Serial": SerialConnectionFactory(),
            "Debug": DebugConnectionFactory(),
            "SIM": SimConnectionFactory(),
        }
        self.setupUi(self)
        self.MySetup()

    def MySetup(self):
        self.typeBox.currentTextChanged.connect(self.connectionChanged)
        self.typeBox.addItems(self.ConnectionFactories.keys())

        self.doneButton.clicked.connect(self.doneButtonPressed)
        comlist = list(map(lambda x: x.device, serial.tools.list_ports.comports()))
        self.comBox.addItems(comlist)

    def doneButtonPressed(self):
        factory = self.ConnectionFactories[self.typeBox.currentText()]
        connection = factory.construct(comPort=self.comBox.currentText(), baudRate=int(self.baudBox.currentText()))
        start.start(connection)
        self.close()

    def connectionChanged(self):
        text = self.typeBox.currentText()
        factory = self.ConnectionFactories[text]

        self.comBox.setEnabled(factory.requiresComPort())
        self.baudBox.setEnabled(factory.requiresBaudRate())



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = comWindow()
    window.show()
    sys.exit(app.exec_())
