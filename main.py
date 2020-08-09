import math
import os
import time
from typing import Union

import PyQt5
from matplotlib import pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
from scipy.misc import imresize

import map_data
import MapBox
import MappingThread
import mplwidget  # DO NOT REMOVE pyinstller needs this
import ReadThread
import SendThread
from detail import LOCAL
from map_data import MapData
from RocketData import RocketData
from SubpacketIDs import SubpacketEnum

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(LOCAL, "main.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

TILES = 14  # TODO Remove if not necessary

# The marker image, used to show where the rocket is on the map UI
# TODO: imresize removed in latest scipy since it's a duplicate from "Pillow". Update and replace.
MAP_MARKER = imresize(plt.imread(MapBox.MARKER_PATH), (12, 12))


class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    sig_send = pyqtSignal(str)

    def __init__(self, connection) -> None:
        """

        :param connection:
        :type connection:
        """
        # TODO move this set of fields out to application.py
        self.connection = connection
        self.data = RocketData()
        self.map = MapData()

        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Hook-up Matplotlib callbacks
        self.plotWidget.canvas.fig.canvas.mpl_connect('resize_event', self.mapResizedEvent)
        # TODO: Also have access to click, scroll, keyboard, etc. Would be good to implement map manipulation.

        self.im = None  # Plot im

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
        self.MappingThread.start()

    def closeEvent(self, event) -> None:
        """

        :param event:
        :type event:
        """
        self.connection.shutDown()
        print("Saving...")
        self.data.save(os.path.join(LOCAL, "finalsave_" + str(int(time.time())) + ".csv"))
        print("Saved!")

    # Updates the UI when new data is available for display
    def receiveData(self) -> None:
        """

        :return:
        :rtype:
        """
        def nonezero(x: float) -> Union[float, None]:
            """

            :param x:
            :type x:
            :return:
            :rtype:
            """
            return 0 if x is None else x

        latitude = self.data.lastvalue(SubpacketEnum.LATITUDE.value)
        longitude = self.data.lastvalue(SubpacketEnum.LONGITUDE.value)
        accel = math.sqrt(nonezero(self.data.lastvalue(SubpacketEnum.ACCELERATION_X.value)) ** 2 +
                          nonezero(self.data.lastvalue(SubpacketEnum.ACCELERATION_Y.value)) ** 2 +
                          nonezero(self.data.lastvalue(SubpacketEnum.ACCELERATION_Z.value)) ** 2)

        self.AltitudeLabel.setText(str(self.data.lastvalue(SubpacketEnum.CALCULATED_ALTITUDE.value)))
        self.MaxAltitudeLabel.setText(str(self.data.highest_altitude))
        self.GpsLabel.setText(str(latitude) + ", " + str(longitude))
        self.StateLabel.setText(str(self.data.lastvalue(SubpacketEnum.STATE.value)))
        self.PressureLabel.setText(str(self.data.lastvalue(SubpacketEnum.PRESSURE.value)))
        self.AccelerationLabel.setText(str(accel))

    def sendButtonPressed(self) -> None:
        """

        """
        word = self.commandEdit.text()
        self.sendCommand(word)
        self.commandEdit.setText("")

    def printToConsole(self, text) -> None:
        """

        :param text:
        :type text:
        """
        self.consoleText.setPlainText(self.consoleText.toPlainText() + text + "\n")
        self.consoleText.moveCursor(QtGui.QTextCursor.End)

    def sendCommand(self, command) -> None:
        """

        :param command:
        :type command:
        """
        self.printToConsole(command)
        self.sig_send.emit(command)

    def saveFile(self) -> None:
        """

        """
        result = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', directory=LOCAL, filter='.csv')
        if result[0]:
            if result[0][-len(result[1]):] == result[1]:
                name = result[0]
            else:
                name = result[0] + result[1]

            self.data.save(name)

    # Updates the UI when a new map is available for display
    def receiveMap(self) -> None:
        """

        """
        children = self.plotWidget.canvas.ax.get_children()
        for c in children:
            if isinstance(c, AnnotationBbox):
                c.remove()

        mapImage = self.map.getMapValue(map_data.IMAGE)

        # plotMap UI modification
        self.plotWidget.canvas.ax.set_axis_off()
        self.plotWidget.canvas.ax.set_ylim(mapImage.shape[0], 0)
        self.plotWidget.canvas.ax.set_xlim(0, mapImage.shape[1])

        # Removes pesky white boarder
        self.plotWidget.canvas.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        if self.im:
            # Required because plotting images over old ones creates memory leak
            # NOTE: im.set_data() can also be used
            self.im.remove()

        self.im = self.plotWidget.canvas.ax.imshow(mapImage)

        # updateMark UI modification
        mark = self.map.getMapValue(map_data.MARK)
        annotation_box = AnnotationBbox(OffsetImage(MAP_MARKER), mark, frameon=False)
        self.plotWidget.canvas.ax.add_artist(annotation_box)

        self.plotWidget.canvas.draw()

    # Called whenever the map plot is resized, also is called once at the start
    def mapResizedEvent(self, event) -> None:
        """

        :param event:
        :type event:
        """
        self.MappingThread.setDesiredMapSize(event.width, event.height)
