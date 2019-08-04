import atexit
import math
import sys
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
import mplwidget #DO NOT REMOVE pyinstller needs this

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

if getattr(sys, 'frozen', False):
    local = os.path.dirname(sys.executable)
elif __file__:
    local = os.path.dirname(__file__)

qtCreatorFile = os.path.join(local, "main.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

TILES = 14

class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    sig_send = pyqtSignal(str)

    def __init__(self, com, baud):
        self.data = RD()
        atexit.register(self.exit_handler)

        self.zoom = 15
        self.lastgps = time.time()
        self.xtile = None
        self.ytile = None

        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.sendButton.clicked.connect(self.sendButtonPressed)
        self.commandEdit.returnPressed.connect(self.sendButtonPressed)
        self.actionSave.triggered.connect(self.data.save)

        self.StatusButton.clicked.connect(lambda _: self.sendCommand("status"))
        self.ArmButton.clicked.connect(lambda _: self.sendCommand("arm"))
        self.HaloButton.clicked.connect(lambda _: self.sendCommand("halo"))

        markerpath = os.path.join(local, "marker.png")
        self.marker = imresize(plt.imread(markerpath), (12,12))
        self.plotMap(51.852667, -111.646972)

        idSet = set(RocketData.chartoname.keys())
        self.printToConsole("Starting Serial")
        self.SThread = SerialThread.SThread(com, idSet, baud)
        self.SThread.sig_received.connect(self.receiveData)
        self.sig_send.connect(self.SThread.queueMessage)
        self.SThread.sig_print.connect(self.printToConsole)
        self.SThread.start()


    def receiveData(self, bytes): #TODO: ARE WE SURE THIS IS THREAD SAFE? USE QUEUE OR PUT IN SERIAL THREAD
        self.data.addpoint(bytes)

        latitude = self.data.lastvalue("Latitude")
        longitude = self.data.lastvalue("Longitude")

        nonezero = lambda x: 0 if x is None else x
        accel = math.sqrt(nonezero(self.data.lastvalue("Acceleration X"))**2 +
                          nonezero(self.data.lastvalue("Acceleration Y"))**2 +
                            nonezero(self.data.lastvalue("Acceleration Z"))**2)

        self.AltitudeLabel.setText(str(self.data.lastvalue("Calculated Altitude")))
        self.MaxAltitudeLabel.setText(str(self.data.highest_altitude))
        self.GpsLabel.setText(str(latitude) + ", " + str(longitude))
        self.StateLabel.setText(str(self.data.lastvalue("State")))
        self.PressureLabel.setText(str(self.data.lastvalue("Pressure")))
        self.AccelerationLabel.setText(str(accel))

        #self.plotMap(latitude, longitude) #Uncomment to make map recenter

        newtime = time.time()
        if newtime - self.lastgps >= 3:
            self.updateMark(latitude, longitude)
        self.lastgps = newtime

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

    def plotMap(self, latitude, longitude):
        p = GoogleMaps.MapPoint(longitude, latitude)
        if longitude is None or latitude is None or (p.getTileX(self.zoom) == self.xtile
                                                               and p.getTileY(self.zoom) == self.ytile):
            return

        location = GoogleMaps.MapPoint(longitude, latitude)
        img = GoogleMaps.getMapImage(location, self.zoom, TILES, TILES)

        self.plotWidget.canvas.ax.set_axis_off()
        self.plotWidget.canvas.ax.set_ylim(TILES*GoogleMaps.TILE_SIZE,0)
        self.plotWidget.canvas.ax.set_xlim(0,TILES * GoogleMaps.TILE_SIZE)

        self.plotWidget.canvas.fig.tight_layout(pad=0, w_pad=0, h_pad=0)
        self.plotWidget.canvas.ax.imshow(img)

        self.plotWidget.canvas.draw()

        self.xtile = location.getTileX(self.zoom)
        self.ytile = location.getTileY(self.zoom)

    def updateMark(self, latitude, longitude):
        if longitude is None or latitude is None:
            return

        children = self.plotWidget.canvas.ax.get_children()
        for c in children:
            if isinstance(c, AnnotationBbox):
                c.remove()

        location = GoogleMaps.MapPoint(longitude, latitude)
        mark = (location.getPixelX(self.zoom) % GoogleMaps.TILE_SIZE + (TILES // 2 + location.getTileX(self.zoom)-self.xtile) * GoogleMaps.TILE_SIZE,
                location.getPixelY(self.zoom) % GoogleMaps.TILE_SIZE + (TILES // 2 + location.getTileY(self.zoom)-self.ytile) * GoogleMaps.TILE_SIZE)
        ab = AnnotationBbox(OffsetImage(self.marker), mark, frameon=False)

        self.plotWidget.canvas.ax.add_artist(ab)
        self.plotWidget.canvas.draw()

    def exit_handler(self):
        print("Saving...")
        self.data.save()
        print("Saved!")

