import math
import time
import threading
import os

import PyQt5
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import pyqtSignal

import matplotlib.pyplot as plt
from scipy.misc import imresize

from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import mplwidget  # DO NOT REMOVE pyinstller needs this

import MapBox
from detail import LOCAL

import ReadThread
import SendThread
import MappingThread
from RocketData import RocketData
from MapData import MapData, MapDataFieldNamesEnum
from SubpacketIDs import SubpacketEnum

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(LOCAL, "main.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

TILES = 14 # TODO Remove if not necessary


class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    sig_send = pyqtSignal(str)

    def __init__(self, connection):
        # TODO move this set of fields out to application.py
        self.connection = connection
        self.data = RocketData()
        self.map = MapData()

        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Attach functions for buttons
        self.sendButton.clicked.connect(self.sendButtonPressed)
        self.commandEdit.returnPressed.connect(self.sendButtonPressed)
        self.actionSave.setShortcut("Ctrl+S")
        self.actionSave.triggered.connect(self.saveFile)

        self.StatusButton.clicked.connect(lambda _: self.sendCommand("status"))
        self.ArmButton.clicked.connect(lambda _: self.sendCommand("arm"))
        self.HaloButton.clicked.connect(lambda _: self.sendCommand("halo"))

        self.printToConsole("Starting Connection")

        # TODO move all these thread controls out to application.py
        # Init and connection of ReadThread
        self.ReadThread = ReadThread.ReadThread(self.connection, self.data)
        self.ReadThread.sig_received.connect(self.receiveData)
        self.ReadThread.sig_print.connect(self.printToConsole)
        self.ReadThread.start()

        # Init and connection of SendThread
        self.SendThread = SendThread.SendThread(self.connection)
        self.sig_send.connect(self.SendThread.queueMessage)
        self.SendThread.sig_print.connect(self.printToConsole)
        self.SendThread.start()

        # Init and connection of MappingThread
        self.MappingThread = MappingThread.MappingThread(self.connection, self.map, self.data)
        self.MappingThread.sig_received.connect(self.receiveMap)
        self.MappingThread.sig_print.connect(self.printToConsole)
        self.data.addNewCallback(SubpacketEnum.LATITUDE.value, self.MappingThread.notify)
        self.data.addNewCallback(SubpacketEnum.LONGITUDE.value, self.MappingThread.notify) # TODO review, could/should be omitted
        self.MappingThread.start()


    def closeEvent(self, event):
        self.connection.shutDown()
        print("Saving...")
        self.data.save(os.path.join(LOCAL, "finalsave_" + str(int(time.time())) + ".csv"))
        print("Saved!")


    # Updates the UI when new data is available for display
    def receiveData(self):
        latitude = self.data.lastvalue(SubpacketEnum.LATITUDE.value)
        longitude = self.data.lastvalue(SubpacketEnum.LONGITUDE.value)

        nonezero = lambda x: 0 if x is None else x
        accel = math.sqrt(nonezero(self.data.lastvalue(SubpacketEnum.ACCELERATION_X.value)) ** 2 +
                          nonezero(self.data.lastvalue(SubpacketEnum.ACCELERATION_Y.value)) ** 2 +
                          nonezero(self.data.lastvalue(SubpacketEnum.ACCELERATION_Z.value)) ** 2)

        self.AltitudeLabel.setText(str(self.data.lastvalue(SubpacketEnum.CALCULATED_ALTITUDE.value)))
        self.MaxAltitudeLabel.setText(str(self.data.highest_altitude))
        self.GpsLabel.setText(str(latitude) + ", " + str(longitude))
        self.StateLabel.setText(str(self.data.lastvalue(SubpacketEnum.STATE.value)))
        self.PressureLabel.setText(str(self.data.lastvalue(SubpacketEnum.PRESSURE.value)))
        self.AccelerationLabel.setText(str(accel))


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

    def saveFile(self):
        result = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', directory=LOCAL, filter='.csv')
        if result[0]:
            if result[0][-len(result[1]):] == result[1]:
                name = result[0]
            else:
                name = result[0] + result[1]

            self.data.save(name)

    # Updates the UI when a new map is available for display
    def receiveMap(self):
        children = self.plotWidget.canvas.ax.get_children()
        for c in children:
            if isinstance(c, AnnotationBbox):
                c.remove()

        mapData = self.map.getMap()

        # plotMap UI modification
        self.plotWidget.canvas.ax.set_axis_off()
        self.plotWidget.canvas.ax.set_ylim(mapData[MapDataFieldNamesEnum.LOCATION.value].height * MapBox.TILE_SIZE, 0)
        self.plotWidget.canvas.ax.set_xlim(0, mapData[MapDataFieldNamesEnum.LOCATION.value].width * MapBox.TILE_SIZE)

        self.plotWidget.canvas.fig.tight_layout(pad=0, w_pad=0, h_pad=0)
        self.plotWidget.canvas.ax.imshow(mapData[MapDataFieldNamesEnum.IMAGE.value])

        self.plotWidget.canvas.draw()

        # updateMark UI modification
        self.plotWidget.canvas.ax.add_artist(mapData[MapDataFieldNamesEnum.ANNO_BOX.value])
        self.plotWidget.canvas.draw()

    # # Draw and show the map on the UI
    # def plotMap(self, latitude, longitude):
    #     p = MapBox.MapPoint(latitude, longitude)
    #
    #     with self.lock:
    #         if longitude is None or latitude is None:
    #             return
    #
    #     lat1 = latitude + self.radius / 110.574
    #     lon1 = longitude - self.radius / 111.320 / math.cos(lat1 * math.pi / 180.0)
    #     p1 = MapBox.MapPoint(lat1, lon1)
    #
    #     lat2 = latitude - self.radius / 110.574
    #     lon2 = longitude + self.radius / 111.320 / math.cos(lat2 * math.pi / 180.0)
    #     p2 = MapBox.MapPoint(lat2, lon2)
    #
    #     # Create MapPoints that correspond to corners of a square area (of side length 2*radius) surrounding the
    #     # inputted latitude and longitude.
    #
    #     location = MapBox.TileGrid(p1, p2, self.zoom)
    #     location.downloadArrayImages()
    #
    #     img = location.genStichedMap()

        # # TODO Moved up into simple function in main
        # self.plotWidget.canvas.ax.set_axis_off()
        # self.plotWidget.canvas.ax.set_ylim(location.height * MapBox.TILE_SIZE, 0)
        # self.plotWidget.canvas.ax.set_xlim(0, location.width * MapBox.TILE_SIZE)
        #
        # self.plotWidget.canvas.fig.tight_layout(pad=0, w_pad=0, h_pad=0)
        # self.plotWidget.canvas.ax.imshow(img)
        #
        # self.plotWidget.canvas.draw()

    # # Update UI with location on plot
    # def updateMark(self, latitude, longitude):
    #     if longitude is None or latitude is None:
    #         return
    #
    #     children = self.plotWidget.canvas.ax.get_children()
    #     for c in children:
    #         if isinstance(c, AnnotationBbox):
    #             c.remove()
    #
    #     p = MapBox.MapPoint(latitude, longitude)
    #
    #     lat1 = latitude + self.radius / 110.574
    #     lon1 = longitude - self.radius / 111.320 / math.cos(lat1 * math.pi / 180.0)
    #     p1 = MapBox.MapPoint(lat1, lon1)
    #
    #     lat2 = latitude - self.radius / 110.574
    #     lon2 = longitude + self.radius / 111.320 / math.cos(lat2 * math.pi / 180.0)
    #     p2 = MapBox.MapPoint(lat2, lon2)
    #
    #     location = MapBox.TileGrid(p1, p2, self.zoom)
    #
    #     x = (p.x - location.xMin) / (location.xMax - location.xMin)
    #     y = (p.y - location.yMin) / (location.yMax - location.yMin)
    #
    #     mark = (x * MapBox.TILE_SIZE * len(location.ta[0]), y * MapBox.TILE_SIZE * len(location.ta))
    #
    #     ab = AnnotationBbox(OffsetImage(self.marker), mark, frameon=False)

        # # TODO Moved up into simple function in main
        # self.plotWidget.canvas.ax.add_artist(ab)
        # self.plotWidget.canvas.draw()

    # # TODO Info
    # def threadLoop(self):
    #     lastgps = time.time()
    #     lastMapUpdate = time.time()
    #     lastLatitude = None
    #     lastLongitude = None
    #     while True:
    #         try:
    #             with self.lock:
    #                 lat = self.latitude
    #                 lon = self.longitude
    #             lastLat = lastLatitude
    #             lastLon = lastLongitude
    #             lmu = lastMapUpdate
    #
    #             if (time.time() - lmu > 5) and not (lat is None or lon is None):
    #                 if lastLat is None or lastLon is None:
    #                     self.plotMap(lat, lon)
    #                     lastLat = lat
    #                     lastLon = lon
    #                     lmu = time.time()
    #                 else:
    #                     if (abs(lat - lastLat) >= self.radius / 110.574) or (
    #                             abs(lon - lastLon) >= self.radius / 111.320 / math.cos(lat * math.pi / 180.0)):
    #                         self.plotMap(lat, lon)
    #                         lastLat = lat
    #                         lastLon = lon
    #                         lmu = time.time()
    #
    #             lastLatitude = lastLat
    #             lastLongitude = lastLon
    #             lastMapUpdate = lmu
    #             lgps = lastgps
    #
    #             if time.time() - lgps >= 1:  # TODO sort out what this code does and if it can handle change to way it uses data
    #                 with self.lock:
    #                     self.updateMark(self.latitude, self.longitude)
    #                 lgps = time.time()
    #
    #             lastgps = lgps
    #
    #         except:
    #             print("Error in map thread loop.")
