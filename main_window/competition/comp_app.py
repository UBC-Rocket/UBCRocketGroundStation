import math
import os
from typing import Callable, Dict
import logging

from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from connections.connection import Connection
from util.detail import LOCAL, BUNDLED_DATA, LOGGER, qtSignalLogHandler, GIT_HASH
from util.event_stats import Event
from profiles.rocket_profile import RocketProfile

from .mapping import map_data, mapbox_utils
from .mapping.mapping_thread import MappingThread
from main_window.main_app import MainApp
from main_window.mplwidget import MplWidget

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "comp_app.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# The marker image, used to show where the rocket is on the map UI
MAP_MARKER = Image.open(mapbox_utils.MARKER_PATH).resize((12, 12), Image.LANCZOS)

LABLES_UPDATED_EVENT = Event('lables_updated')
MAP_UPDATED_EVENT = Event('map_updated')


class CompApp(MainApp, Ui_MainWindow):

    def __init__(self, connections: Dict[str, Connection], rocket_profile: RocketProfile) -> None:
        """

        :param connection:
        :type connection: Connection
        :param rocket_profile:
        :type rocket_profile: RocketProfile
        """
        super().__init__(connections, rocket_profile)

        self.map = map_data.MapData()

        self.im = None  # Plot im

        # Attach functions for static buttons
        self.sendButton.clicked.connect(self.send_button_pressed)
        self.commandEdit.returnPressed.connect(self.send_button_pressed)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave.setShortcut("Ctrl+S")
        self.actionReset.triggered.connect(self.reset_view)

        # Hook-up logger to UI text output
        # Note: Currently doesnt print logs from other processes (e.g. mapping process)
        log_format = logging.Formatter("[%(asctime)s] (%(levelname)s) %(message)s")
        log_handler = qtSignalLogHandler(exception_traces=False)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(log_format)
        log_handler.qt_signal.connect(self.print_to_ui)
        LOGGER.addHandler(log_handler)

        self.setup_buttons()
        self.setup_labels()
        self.setup_subwindow().showMaximized()

        self.setWindowIcon(QtGui.QIcon(mapbox_utils.MARKER_PATH))

        self.original_geometry = self.saveGeometry()
        self.original_state = self.saveState()
        self.settings = QtCore.QSettings('UBCRocket', 'UBCRGS')
        self.restore_view()

        # Init and connection of MappingThread
        self.MappingThread = MappingThread(self.connections, self.map, self.rocket_data, self.rocket_profile)
        self.MappingThread.sig_received.connect(self.receive_map)
        self.MappingThread.start()

        LOGGER.info(f"Successfully started app (version = {GIT_HASH})")

    def setup_buttons(self):
        """Create all of the buttons for the loaded rocket profile."""

        grid_width = math.ceil(math.sqrt(len(self.rocket_profile.buttons)))

        # Trying to replicate PyQt's generated code from a .ui file as closely as possible. This is why setattr is
        # being used to keep all of the buttons as named attributes of MainApp and not elements of a list.
        row = 0
        col = 0
        for button in self.rocket_profile.buttons:
            qt_button = QtWidgets.QPushButton(self.centralwidget)
            setattr(self, button + "Button", qt_button)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            sizePolicy.setHeightForWidth(getattr(self, button + "Button").sizePolicy().hasHeightForWidth())
            qt_button.setSizePolicy(sizePolicy)
            font = QtGui.QFont()
            font.setPointSize(16)
            font.setKerning(True)
            qt_button.setFont(font)
            qt_button.setObjectName(f"{button}Button")
            self.commandButtonGrid.addWidget(qt_button, row, col, 1, 1)
            if col + 1 < grid_width:
                col += 1
            else:
                col = 0
                row += 1
        # A .py file created from a .ui file will have the labels all defined at the end, for some reason. Two for loops
        # are being used to be consistent with the PyQt5 conventions.
        for button in self.rocket_profile.buttons:
            getattr(self, button + "Button").setText(QtCore.QCoreApplication.translate('MainWindow', button))

        def gen_send_command(cmd: str) -> Callable[[], None]:
            """Creates a function that sends the given command to the console."""

            def send() -> None:
                self.send_command(cmd)

            return send

        # Connecting to a more traditional lambda expression would not work in this for loop. It would cause all of the
        # buttons to map to the last command in the list, hence the workaround with the higher order function.
        for button, command in self.rocket_profile.buttons.items():
            getattr(self, button + "Button").clicked.connect(gen_send_command(command))

    def setup_labels(self):
        """Create all of the data labels for the loaded rocket profile."""

        # Trying to replicate PyQt's generated code from a .ui file as closely as possible. This is why setattr is
        # being used to keep all of the buttons as named labels of MainApp and not elements of a list.
        for label in self.rocket_profile.labels:
            name = label.name

            qt_text = QtWidgets.QLabel(self.centralwidget)
            setattr(self, name + "Text", qt_text)
            qt_text.setObjectName(f"{name}Text")

            qt_label = QtWidgets.QLabel(self.centralwidget)
            setattr(self, name + "Label", qt_label)
            qt_label.setObjectName(f"{name}Label")

            self.dataLabelFormLayout.addRow(qt_text, qt_label)

        # A .py file created from a .ui file will have the labels all defined at the end, for some reason. Two for loops
        # are being used to be consistent with the PyQt5 conventions.
        for label in self.rocket_profile.labels:
            name = label.name
            getattr(self, name + "Text").setText(QtCore.QCoreApplication.translate("MainWindow", label.display_name))
            getattr(self, name + "Label").setText(QtCore.QCoreApplication.translate("MainWindow", "0"))

    def setup_subwindow(self):
        self.plotWidget = MplWidget()
        # Hook-up Matplotlib callbacks
        self.plotWidget.canvas.fig.canvas.mpl_connect('resize_event', self.map_resized_event)
        # TODO: Also have access to click, scroll, keyboard, etc. Would be good to implement map manipulation.

        sub = QtWidgets.QMdiSubWindow()
        sub.layout().setContentsMargins(0, 0, 0, 0)
        sub.setWidget(self.plotWidget)
        sub.setWindowTitle("Data Plot")
        sub.setWindowIcon(QtGui.QIcon(mapbox_utils.MARKER_PATH))

        self.mdiArea.addSubWindow(sub)
        sub.show()

        return sub

    def receive_data(self) -> None:
        """
        This is called when new data is available to be displayed.
        :return:
        :rtype:
        """

        for label in self.rocket_profile.labels:
            getattr(self, label.name + "Label").setText(
                label.update(self.rocket_data)
            )

        LABLES_UPDATED_EVENT.increment()

    def send_button_pressed(self) -> None:
        """

        """
        word = self.commandEdit.text()
        self.send_command(word)
        self.commandEdit.setText("")

    def print_to_ui(self, text) -> None:
        """
        This is called when a thread wants to show a message in the UI
        :param text:
        :type text:
        """
        current_text = self.consoleText.toPlainText()

        if len(current_text) == 0:
            new_text = text

        else:
            lines = current_text.split('\n')
            lines.append(text)

            # Limit to 100 lines
            lines = lines[-100:]

            new_text = "\n".join(lines)

        self.consoleText.setPlainText(new_text)
        self.consoleText.moveCursor(QtGui.QTextCursor.End)

    def send_command(self, command) -> None:
        """
        Call this to send a command
        :param command:
        :type command:
        """
        self.print_to_ui(command)
        super().send_command(command)

    def save_file(self) -> None:
        """

        """
        result = QtWidgets.QFileDialog.getSaveFileName(None, 'Save File', directory=LOCAL, filter='.csv')
        if result[0]:
            if result[0][-len(result[1]):] == result[1]:
                name = result[0]
            else:
                name = result[0] + result[1]

            self.rocket_data.save(name)

    def reset_view(self) -> None:
        self.restoreGeometry(self.original_geometry)
        self.restoreState(self.original_state)

        for sub in self.mdiArea.subWindowList():
            sub.close()
        self.setup_subwindow().showMaximized()

    def save_view(self):
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

    def restore_view(self):
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        state = self.settings.value("windowState")
        if state is not None:
            self.restoreState(state)

    def receive_map(self) -> None:
        """
        Updates the UI when a new map is available for display
        """
        children = self.plotWidget.canvas.ax.get_children()
        for c in children:
            if isinstance(c, AnnotationBbox):
                c.remove()

        zoom, radius, map_image, mark = self.map.get_map_value()

        # plotMap UI modification
        self.plotWidget.canvas.ax.set_axis_off()
        self.plotWidget.canvas.ax.set_ylim(map_image.shape[0], 0)
        self.plotWidget.canvas.ax.set_xlim(0, map_image.shape[1])

        # Removes pesky white boarder
        self.plotWidget.canvas.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        if self.im:
            # Required because plotting images over old ones creates memory leak
            # NOTE: im.set_data() can also be used
            self.im.remove()

        self.im = self.plotWidget.canvas.ax.imshow(map_image)

        # updateMark UI modification
        annotation_box = AnnotationBbox(OffsetImage(MAP_MARKER), mark, frameon=False)
        self.plotWidget.canvas.ax.add_artist(annotation_box)

        # For debugging marker position
        #self.plotWidget.canvas.ax.plot(mark[0], mark[1], marker='o', markersize=3, color="red")

        self.plotWidget.canvas.draw()

        MAP_UPDATED_EVENT.increment()

    def map_resized_event(self, event) -> None:
        """
        Called whenever the map plot is resized, also is called once at the start
        :param event:
        :type event:
        """
        self.MappingThread.setDesiredMapSize(event.width, event.height)

    def shutdown(self):
        self.save_view()
        self.MappingThread.shutdown()
        super().shutdown()


