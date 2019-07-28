import sys
import PyQt5
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import os
import start
import serial.tools.list_ports

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

if getattr(sys, 'frozen', False):
    local = os.path.dirname(sys.executable)
elif __file__:
    local = os.path.dirname(__file__)

qtCreatorFile = os.path.join(local, "comWindow.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class comWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.MySetup()

    def MySetup(self):
        self.doneButton.clicked.connect(self.doneButtonPressed)
        comlist = list(map(lambda x: x.device, serial.tools.list_ports.comports()))
        self.comBox.addItems(comlist)

    def doneButtonPressed(self):
        '''
        while not com:
            var = input("Please enter a COM #: ")
            try:
                com = int(var)
            except:
                print("bad int")
        '''

        start.start(self.comBox.currentText(), int(self.baudBox.currentText()))
        self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = comWindow()
    window.show()
    sys.exit(app.exec_())

