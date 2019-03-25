import atexit
import time

import PyQt5
from PyQt5 import QtCore, QtGui, uic, QtWidgets
import os

from PyQt5.QtCore import pyqtSignal
import matplotlib.pyplot as plt
from scipy.misc import imresize

from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import SerialThread
import GoogleMaps
import RocketData
from RocketData import RocketData as RD

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


py_path = os.path.dirname(os.path.abspath(__file__))
qtCreatorFile = os.path.join(py_path, "main.ui")  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

TILES = 5

ZOOM = 19

class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    sig_send = pyqtSignal(str)

    def __init__(self, com, baud):
        self.data = RD()
        atexit.register(self.exit_handler)

        self.lastgps = time.time()
        self.longitude = -1
        self.latitude = -1

        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.sendButton.clicked.connect(self.sendButtonPressed)
        self.actionSave.triggered.connect(self.data.save)

        self.StatusButton.clicked.connect(lambda _: self.sendCommand("status"))
        self.ArmButton.clicked.connect(lambda _: self.sendCommand("arm"))
        self.HaloButton.clicked.connect(lambda _: self.sendCommand("halo"))

        idSet = set(RocketData.chartoname.keys())
        self.printToConsole("Starting Serial")
        self.SThread = SerialThread.SThread(com, idSet, baud)
        self.SThread.sig_received.connect(self.receiveData)
        self.sig_send.connect(self.SThread.send)
        self.SThread.sig_print.connect(self.printToConsole)
        self.SThread.start()

        local = os.path.dirname(os.path.realpath(__file__))
        markerpath = os.path.join(local, "marker.png")
        self.marker = imresize(plt.imread(markerpath), (12,12))


    def receiveData(self, bytes):
        self.data.addpoint(bytes)

        fresh = False
        if self.longitude == -1 or self.latitude == -1:
            fresh = True

        self.latitude = self.data.lastvalue("Latitude")
        self.longitude = self.data.lastvalue("Longitude")

        if fresh and self.longitude != -1 and self.latitude !=-1:
            self.plotMap()

        self.AltitudeLabel.setText(str(self.data.lastvalue("Calculated Altitude")))
        self.GpsLabel.setText(str(self.latitude) + ", " + str(self.longitude))
        self.StateLabel.setText(str(self.data.lastvalue("State")))
        self.PressureLabel.setText(str(self.data.lastvalue("Pressure")))
        self.AccelerationLabel.setText(str(max(self.data.lastvalue("Acceleration X"),self.data.lastvalue("Acceleration Y"),self.data.lastvalue("Acceleration Z"))))

        self.updateMark()

    def sendButtonPressed(self):
        word = self.commandEdit.text()
        self.sendCommand(word)
        self.commandEdit.setText("")


    def printToConsole(self, text):
        self.consoleText.setPlainText(self.consoleText.toPlainText() + text + "\n")
        self.consoleText.moveCursor(QtGui.QTextCursor.End)

    def sendCommand(self, command):
        self.printToConsole(command)
        self.sig_send.emit(command)

    def plotMap(self):

        location = GoogleMaps.MapPoint(self.longitude, self.latitude)
        img = GoogleMaps.getMapImage(location, ZOOM, TILES, TILES)

        self.plotWidget.canvas.ax.set_axis_off()
        self.plotWidget.canvas.ax.set_ylim(TILES*GoogleMaps.TILE_SIZE,0)
        self.plotWidget.canvas.ax.set_xlim(0,TILES * GoogleMaps.TILE_SIZE)


        self.plotWidget.canvas.fig.tight_layout(pad=0, w_pad=0, h_pad=0)
        self.plotWidget.canvas.ax.imshow(img)

        self.plotWidget.canvas.draw()

    def updateMark(self):
        newtime = time.time()
        if newtime - self.lastgps < 4:
            return
        self.lastgps = newtime

        children = self.plotWidget.canvas.ax.get_children()
        for c in children:
            if isinstance(c, AnnotationBbox):
                c.remove()

        location = GoogleMaps.MapPoint(self.longitude, self.latitude)
        mark = (location.getPixelX(ZOOM) % GoogleMaps.TILE_SIZE + TILES // 2 * GoogleMaps.TILE_SIZE,
                location.getPixelY(ZOOM) % GoogleMaps.TILE_SIZE + TILES // 2 * GoogleMaps.TILE_SIZE)
        ab = AnnotationBbox(OffsetImage(self.marker), mark, frameon=False)

        self.plotWidget.canvas.ax.add_artist(ab)
        self.plotWidget.canvas.draw()

    def exit_handler(self):
        print("Saving...")
        self.data.save()
        print("Saved!")


#print('Press and release your desired shortcut: ')
#shortcut = keyboard.read_hotkey()
#print('Shortcut selected:', shortcut)
#keyboard.add_hotkey(shortcut, on_triggered)
