import math
import os
from typing import Callable

import PyQt5
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal

from connections.connection import Connection
from util.detail import LOCAL, BUNDLED_DATA, LOGS_DIR, SESSION_ID, LOGGER
from util.event_stats import Event
from profiles.rocket_profile import RocketProfile

from .mapping import map_data, mapbox_utils
from .mapping.mapping_thread import MappingThread
from .read_thread import ReadThread
from .rocket_data import RocketData
from .send_thread import SendThread

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "main.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# The marker image, used to show where the rocket is on the map UI
MAP_MARKER = Image.open(mapbox_utils.MARKER_PATH).resize((12, 12), Image.LANCZOS)

LABLES_UPDATED_EVENT = Event('lables_updated')
MAP_UPDATED_EVENT = Event('map_updated')

class MainApp(QtWidgets.QMainWindow, Ui_MainWindow):
    sig_send = pyqtSignal(str)

    def __init__(self, connection: Connection, rocket_profile: RocketProfile) -> None:
        """

        :param connection:
        :type connection: Connection
        :param rocket_profile:
        :type rocket_profile: RocketProfile
        """
        self.connection = connection
        self.rocket_profile = rocket_profile
        self.rocket_data = RocketData()
        self.map = map_data.MapData()

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

        self.setup_buttons()
        self.setup_labels()

        self.printToConsole("Starting Connection")

        # Init and connection of ReadThread
        self.ReadThread = ReadThread(self.connection, self.rocket_data)
        self.ReadThread.sig_received.connect(self.receiveData)
        self.ReadThread.sig_print.connect(self.printToConsole)
        self.ReadThread.start()

        # Init and connection of SendThread
        self.SendThread = SendThread(self.connection)
        self.sig_send.connect(self.SendThread.queueMessage)
        self.SendThread.sig_print.connect(self.printToConsole)
        self.SendThread.start()

        # Init and connection of MappingThread
        self.MappingThread = MappingThread(self.connection, self.map, self.rocket_data)
        self.MappingThread.sig_received.connect(self.receiveMap)
        self.MappingThread.sig_print.connect(self.printToConsole)
        self.MappingThread.start()

    def setup_buttons(self):
        """Create all of the buttons for the loaded rocket profile."""

        grid_width = math.ceil(math.sqrt(len(self.rocket_profile.buttons)))

        # Trying to replicate PyQt's generated code from a .ui file as closely as possible. This is why setattr is
        # being used to keep all of the buttons as named attributes of MainApp and not elements of a list.
        row = 0
        col = 0
        for button in self.rocket_profile.buttons.keys():
            qt_button = QtWidgets.QPushButton(self.centralwidget)
            setattr(self, button + "Button", qt_button)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(getattr(self, button + "Button").sizePolicy().hasHeightForWidth())
            qt_button.setSizePolicy(sizePolicy)
            font = QtGui.QFont()
            font.setPointSize(35)
            font.setKerning(True)
            qt_button.setFont(font)
            qt_button.setObjectName(f"{button}Button")
            self.gridLayout_5.addWidget(qt_button, row, col, 1, 1)
            if col + 1 < grid_width:
                col += 1
            else:
                col = 0
                row += 1
        # A .py file created from a .ui file will have the labels all defined at the end, for some reason. Two for loops
        # are being used to be consistent with the PyQt5 conventions.
        for button in self.rocket_profile.buttons.keys():
            getattr(self, button + "Button").setText(QtCore.QCoreApplication.translate('MainWindow', button))

        def gen_send_command(cmd: str) -> Callable[[], None]:
            """Creates a function that sends the given command to the console."""
            def send() -> None:
                self.sendCommand(cmd)
            return send
        # Connecting to a more traditional lambda expression would not work in this for loop. It would cause all of the
        # buttons to map to the last command in the list, hence the workaround with the higher order function.
        for button, command in self.rocket_profile.buttons.items():
            getattr(self, button + "Button").clicked.connect(gen_send_command(command))

    def setup_labels(self):
        """Create all of the data labels for the loaded rocket profile."""

        # Trying to replicate PyQt's generated code from a .ui file as closely as possible. This is why setattr is
        # being used to keep all of the buttons as named labels of MainApp and not elements of a list.
        row = 0
        for label in self.rocket_profile.labels:
            name = label.name
            qt_text = QtWidgets.QLabel(self.centralwidget)
            setattr(self, name + "Text", qt_text)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(getattr(self, name + "Text").sizePolicy().hasHeightForWidth())
            qt_text.setSizePolicy(sizePolicy)
            qt_text.setObjectName(f"{name}Text")
            self.gridLayout_6.addWidget(qt_text, row, 0, 1, 1)

            qt_label = QtWidgets.QLabel(self.centralwidget)
            setattr(self, name + "Label", qt_label)
            qt_label.setObjectName(f"{name}Label")
            self.gridLayout_6.addWidget(qt_label, row, 1, 1, 1)
            row += 1
        # A .py file created from a .ui file will have the labels all defined at the end, for some reason. Two for loops
        # are being used to be consistent with the PyQt5 conventions.
        for label in self.rocket_profile.labels:
            name = label.name
            getattr(self, name + "Text").setText(QtCore.QCoreApplication.translate("MainWindow", label.display_name))
            getattr(self, name + "Label").setText(QtCore.QCoreApplication.translate("MainWindow", "0"))

    def closeEvent(self, event) -> None:
        """

        :param event:
        :type event:
        """
        self.connection.shutDown()
        LOGGER.info("Saving...")
        self.rocket_data.save(os.path.join(LOGS_DIR, "finalsave_" + SESSION_ID + ".csv"))
        LOGGER.info("Saved!")

    # Updates the UI when new data is available for display
    def receiveData(self) -> None:
        """

        :return:
        :rtype:
        """

        for label in self.rocket_profile.labels:
            getattr(self, label.name + "Label").setText(
                label.update(self.rocket_data)
            )

        LABLES_UPDATED_EVENT.increment()

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

            self.rocket_data.save(name)

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

        MAP_UPDATED_EVENT.increment()

    # Called whenever the map plot is resized, also is called once at the start
    def mapResizedEvent(self, event) -> None:
        """

        :param event:
        :type event:
        """
        self.MappingThread.setDesiredMapSize(event.width, event.height)
