"""
Competition app
"""

import math
import os
from typing import Callable, Dict
import logging

from PyQt5.QtWidgets import QAction
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PIL import Image

from connections.connection import Connection
from profiles.label import Label
from profiles.rocket_profile import RocketProfile
from util.detail import LOCAL, BUNDLED_DATA, LOGGER, qtSignalLogHandler, qtHook, GIT_HASH
from util.event_stats import Event

from main_window.main_app import MainApp
from main_window.mplwidget import MplWidget
from .mapping import map_data, mapbox_utils
from .mapping.mapping_thread import MappingThread
from ..accel_widget import AccelWidget

qtCreatorFile = os.path.join(BUNDLED_DATA, "qt_files", "comp_app.ui")

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# The marker image, used to show where the rocket is on the map UI
MAP_MARKER = Image.open(mapbox_utils.MARKER_PATH).resize((12, 12), Image.LANCZOS)

LABELS_UPDATED_EVENT = Event('labels_updated')
MAP_UPDATED_EVENT = Event('map_updated')


class CompApp(MainApp, Ui_MainWindow):
    """
    Comp app
    """

    def __init__(self, connections: Dict[str, Connection], rocket_profile: RocketProfile) -> None:
        """

        :param connections:
        :param rocket_profile:
        """
        super().__init__(connections, rocket_profile)

        self.plot_widget = AccelWidget()
        self.map_data = map_data.MapData()
        self.im = None  # Plot im

        self.command_history = []
        self.command_history_index = None

        # Attach functions for static buttons
        self.sendButton.clicked.connect(self.send_button_pressed)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave.setShortcut("Ctrl+S")
        self.actionReset.triggered.connect(self.reset_view)

        # Hook into some of commandEdit's events
        qtHook(self.commandEdit, 'focusNextPrevChild', lambda _: False,
               override_return=True)  # Prevents tab from changing focus
        qtHook(self.commandEdit, 'keyPressEvent', self.command_edit_key_pressed)
        qtHook(self.commandEdit, 'showPopup', self.command_edit_show_popup)

        # Hook-up logger to UI text output
        # Note: Currently doesn't print logs from other processes (e.g. mapping process)
        log_format = logging.Formatter("[%(asctime)s] (%(levelname)s) %(message)s")
        log_handler = qtSignalLogHandler(exception_traces=False)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(log_format)
        log_handler.qt_signal.connect(self.print_to_ui)
        LOGGER.addHandler(log_handler)

        # Setup dynamic UI elements
        self.setup_buttons()
        self.selected_label = None
        self.setup_labels()
        self.label_windows = {label: None for label in self.rocket_profile.all_labels}
        self.setup_subwindow().showMaximized()
        self.setup_view_menu()
        self.setWindowIcon(QtGui.QIcon(mapbox_utils.MARKER_PATH))

        # Setup user window preferences
        self.original_geometry = self.saveGeometry()
        self.original_state = self.saveState()
        self.settings = QtCore.QSettings('UBCRocket', 'UBCRGS')
        self.restore_view()

        # Init and connection of MappingThread
        self.MappingThread = MappingThread(
            self.connections, self.map_data, self.rocket_data, self.rocket_profile)
        self.MappingThread.sig_received.connect(self.map_callback)
        self.MappingThread.start()

        self.setup_zoom_slider()  # have to set up after mapping thread created

        LOGGER.info(f"Successfully started app (version = {GIT_HASH})")

    def setup_buttons(self):
        """Create all of the buttons for the loaded rocket profile."""

        grid_width = math.ceil(math.sqrt(len(self.rocket_profile.buttons)))

        # Trying to replicate PyQt's generated code from a .ui file
        # as closely as possible. This is why setattr is being used to
        # keep all of the buttons as named attributes of MainApp
        # and not elements of a list.
        row = 0
        col = 0
        for button in self.rocket_profile.buttons:
            qt_button = QtWidgets.QPushButton(self.centralwidget)
            setattr(self, button + "Button", qt_button)
            size_policy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            size_policy.setHeightForWidth(
                getattr(self, button + "Button").sizePolicy().hasHeightForWidth())
            qt_button.setSizePolicy(size_policy)
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
        # A .py file created from a .ui file will have the labels all
        # defined at the end, for some reason. Two for loops are being
        # used to be consistent with the PyQt5 conventions.

        for button in self.rocket_profile.buttons:
            getattr(self, button + "Button").setText(
                QtCore.QCoreApplication.translate('MainWindow', button))

        def gen_send_command(cmd: str) -> Callable[[], None]:
            """Creates a function that sends the given command to the console."""

            def send() -> None:
                self.send_command(cmd)

            return send

        # Connecting to a more traditional lambda expression would not work in this for loop.
        # It would cause all of the buttons to map to the last command in the list,
        # hence the workaround with the higher order function.
        for button, command in self.rocket_profile.buttons.items():
            getattr(self, button + "Button").clicked.connect(gen_send_command(command))

    def setup_labels(self):
        """Create all of the data labels for the loaded rocket profile."""

        def gen_clicked_callback(label: Label):
            def mousePressEvent(QMouseEvent):
                self.selected_label = label
                if self.plot_widget.showing_checkboxes:
                    self.plot_widget.hide_checkboxes()

            return mousePressEvent

        # Trying to replicate PyQt's generated code from a .ui file as closely as possible.
        # This is why setattr is being used to keep all of the buttons as named labels of
        # MainApp and not elements of a list.
        for label in self.rocket_profile.labels:
            name = label.name

            qt_text = QtWidgets.QLabel(self.centralwidget)
            setattr(self, name + "Text", qt_text)
            qt_text.setObjectName(f"{name}Text")

            qt_label = QtWidgets.QLabel(self.centralwidget)
            setattr(self, name + "Label", qt_label)
            qt_label.setObjectName(f"{name}Label")

            self.dataLabelFormLayout.addRow(qt_text, qt_label)

            if label.map_fn is not None:
                qt_text.mousePressEvent = gen_clicked_callback(label)

            if "GPS" in label.name:
                self.selected_label = label

        if self.selected_label is None:
            self.selected_label = self.rocket_profile.labels[0]

        # A .py file created from a .ui file will have the labels all defined at
        # the end, for some reason. Two for loops are being used to be consistent
        # with the PyQt5 conventions.
        for label in self.rocket_profile.labels:
            name = label.name
            getattr(self, name + "Text").setText(
                QtCore.QCoreApplication.translate("MainWindow", label.display_name + ":"))
            getattr(self, name + "Label").setText(
                QtCore.QCoreApplication.translate("MainWindow", ""))

    def map_callback(self):
        """
        Update map and data plots
        """
        # plot in main window
        if "GPS" in self.selected_label.name:
            MAP_UPDATED_EVENT.increment()
            self.selected_label.map_fn(self)
        else:
            self.selected_label.map_fn(self, self.plot_widget, self.selected_label)

        # plot in other open windows
        for label in self.label_windows:
            window = self.label_windows[label]
            if window:
                try:  # window may have been closed
                    label.map_fn(self, window, label)
                except RuntimeError as e:  # catches canvas deleted exception
                    self.label_windows[label] = None

    def setup_subwindow(self):
        """Create subwindows for plotting time series data"""
        # Hook-up Matplotlib callbacks
        self.plot_widget.canvas.fig.canvas.mpl_connect('resize_event', self.map_resized_event)
        #TODO: Also have access to click, scroll, keyboard, etc.
        # Would be good to implement map manipulation.

        sub = QtWidgets.QMdiSubWindow()
        sub.layout().setContentsMargins(0, 0, 0, 0)
        sub.setWidget(self.plot_widget)
        sub.setWindowTitle("Data Plot")
        sub.setWindowIcon(QtGui.QIcon(mapbox_utils.MARKER_PATH))

        self.mdiArea.addSubWindow(sub)
        sub.show()

        return sub

    def setup_view_menu(self) -> None:
        """Create menu used to choose data for plot"""
        view_menu = self.menuBar().children()[2]

        # Menu bar for choosing rocket device view
        if len(self.rocket_profile.mapping_devices) > 1:
            map_view_menu = view_menu.addMenu("Map")

            view_all = QAction("All", self)
            all_devices = self.rocket_profile.mapping_devices
            view_all.triggered.connect(lambda i, devices=all_devices: self.set_view_device(devices))
            map_view_menu.addAction(view_all)

            for device in self.rocket_profile.mapping_devices:
                view_device = QAction(f'{device}', self)
                view_device.triggered.connect(
                    lambda i, mapping_device=device: self.set_view_device([mapping_device]))
                map_view_menu.addAction(view_device)

        # Menu bar for choosing which data to plot
        dataplot_view_menu = view_menu.addMenu("Data Plot")

        for label in self.label_windows:
            if "GPS" not in label.name:
                data_label = QAction(f'{label.name}', self)
                data_label.triggered.connect(
                    lambda i, label_name=label: self.open_plot_window(label_name))
                dataplot_view_menu.addAction(data_label)

    def setup_zoom_slider(self) -> None:
        """Set up slider and buttons for map zooming"""
        max_zoom_factor = 3  # zoom out 2**3 scale
        min_zoom_factor = -2
        self.num_ticks_per_scale = 1
        # each tick represents a 2x scale change
        # increase num_ticks_per_scale for more ticks on slider

        self.horizontalSlider.setMinimum(min_zoom_factor * self.num_ticks_per_scale)
        self.horizontalSlider.setMaximum(max_zoom_factor * self.num_ticks_per_scale)
        self.horizontalSlider.setValue(0)  # default original scale
        self.horizontalSlider.valueChanged.connect(self.map_zoomed)

        self.zoom_in_button.clicked.connect(self.slider_dec)
        self.zoom_out_button.clicked.connect(self.slider_inc)

    def receive_data(self) -> None:
        """
        This is called when new data is available to be displayed.
        :return:
        :rtype:
        """

        for label in self.rocket_profile.labels:
            try:
                getattr(self, label.name + "Label").setText(
                    label.update(self.rocket_data)
                )
            except:
                LOGGER.exception('Failed to update %s Label:', label.name)

        LABELS_UPDATED_EVENT.increment()

    def send_button_pressed(self) -> None:
        """
        Update command history
        """
        command = self.commandEdit.currentText()
        self.send_command(command)
        self.commandEdit.setCurrentText("")

        # Reset index to reflect that we are no longer viewing history
        self.command_history_index = None

        # Update command history (if command isn't a repeat)
        if len(self.command_history) == 0 or command != self.command_history[-1]:
            self.command_history.append(command)
            self.command_history = self.command_history[-50:]  # Limit history to 50

    def command_edit_show_popup(self):
        """
        :return: True to suppress the event
        """

        # Update list of commands
        self.commandEdit.clear()
        self.commandEdit.addItems(sorted(self.command_parser.available_commands()))

        # Doesn't behave as expected if there's still text in the edit box
        self.commandEdit.setCurrentText('')
        return False

    def command_edit_key_pressed(self, event):
        """
        :return: True to suppress the event
        """
        # Switch based on key
        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):  # Enter -- Send command
            self.send_button_pressed()

        elif event.key() == QtCore.Qt.Key_Up:  # Up arrow key -- Go back in history
            if self.commandEdit.view().isVisible():  # Do not handle if user is browsing popup list
                return False

            # Calculate next index in history
            if self.command_history_index is not None:
                # Currently browsing history, go back one
                self.command_history_index = max(self.command_history_index - 1, 0)
            elif len(self.command_history) > 0:
                # Was not browsing history, but history is available. Go to first item in history.
                self.command_history_index = len(self.command_history) - 1
            else:
                # End of history, do nothing
                return True

            # Set text based on index in history
            self.commandEdit.setCurrentText(self.command_history[self.command_history_index])
            return True

        elif event.key() == QtCore.Qt.Key_Down:  # Down arrow key -- Go forward in history
            if self.commandEdit.view().isVisible():  # Do not handle if user is browsing popup list
                return False

            if self.command_history_index is not None:
                if self.command_history_index == len(self.command_history) - 1:
                    # Reached present command
                    self.command_history_index = None
                    self.commandEdit.setCurrentText('')
                else:
                    # Go forward one item in history
                    self.command_history_index = min(
                        self.command_history_index + 1, len(self.command_history) - 1)
                    self.commandEdit.setCurrentText(
                        self.command_history[self.command_history_index])
            return True

        elif event.key() == QtCore.Qt.Key_Tab:  # Tab -- Autocomplete command
            input = self.commandEdit.currentText().upper()

            # Find commands that match input
            common_commands = [command for command in self.command_parser.available_commands()
                               if command.upper()[0:len(input)] == input]

            if len(common_commands) > 0:  # Check that we found at lest one command that matches

                # Figure out how many characters are common between all matching commands
                common_index = 0
                while all(x[common_index] == common_commands[0][common_index]
                          if len(x) > common_index else False
                          for x in common_commands):
                    common_index += 1
                common_portion = common_commands[0][0:common_index]

                if len(common_portion) > len(input) or len(common_commands) == 1:
                    # Found match, autocomplete
                    self.commandEdit.setCurrentText(common_portion)
                elif len(common_commands) > 10:
                    # Too many branching possibilities
                    self.print_to_ui(f"Too many possibilities to show... ({len(common_commands)})")
                elif len(common_commands) > 0:
                    # Print branching possibilities
                    self.print_to_ui('\n'.join(common_commands))

            return True

        else:  # All other keys
            # To avoid qComboBox's shitty "autocomplete"
            self.commandEdit.clear()
            return False

        return False

    def print_to_ui(self, text) -> None:
        """
        This is called when a thread wants to show a message in the UI
        :param text:
        :type text:
        """
        current_text = self.consoleText.toPlainText()

        if len(current_text) == 0:
            lines = []  # prevents empty first line
        else:
            lines = current_text.split('\n')

        lines += text.split('\n')

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
        self.print_to_ui(f">>> {command}")
        super().send_command(command)

    def save_file(self) -> None:
        """ Save """
        result = QtWidgets.QFileDialog.getSaveFileName(
            None, 'Save File', directory=LOCAL, filter='.csv')
        if result[0]:
            if result[0][-len(result[1]):] == result[1]:
                name = result[0]
            else:
                name = result[0] + result[1]

            self.rocket_data.save(name)

    def reset_view(self) -> None:
        """Reset window"""
        original_position = self.geometry().center()
        self.restoreGeometry(self.original_geometry)
        self.restoreState(self.original_state)

        # Workaround for known Qt issue.
        # See section on X11 in https://doc.qt.io/qt-5/restoring-geometry.html
        geometry = self.frameGeometry()
        geometry.moveCenter(original_position)
        self.move(geometry.topLeft())

        for sub in self.mdiArea.subWindowList():
            sub.close()
            sub.deleteLater()
            # Required to prevent memory leak. Also deletes window sub-objects (plot widget, etc.)

        self.setup_subwindow().showMaximized()

    def save_view(self):
        """View settings"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

    def restore_view(self):
        """Restore view"""
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        state = self.settings.value("windowState")
        if state is not None:
            self.restoreState(state)

    def map_resized_event(self, event) -> None:
        """
        Called whenever the map plot is resized, also is called once at the start
        :param event:
        :type event:
        """
        self.MappingThread.setDesiredMapSize(event.width, event.height)

    def set_view_device(self, viewed_devices) -> None:
        """Change view device"""
        self.MappingThread.setViewedDevice(viewed_devices)

    def slider_inc(self) -> None:
        """Increase zoom"""
        self.horizontalSlider.setValue(self.horizontalSlider.value() + 1)

    def slider_dec(self) -> None:
        """Decrease zoom"""
        self.horizontalSlider.setValue(self.horizontalSlider.value() - 1)

    def map_zoomed(self) -> None:
        """Set zoom setting"""
        self.MappingThread.setMapZoom(2 ** (self.horizontalSlider.value() / self.num_ticks_per_scale))

    def open_plot_window(self, label) -> None:
        """
        Opens new window for plotting data when selected from menu bar
        :param label:
        """
        window = self.label_windows[label]

        if window is None:
            new_window = AccelWidget() if "Acceleration" in label.name else MplWidget()
            new_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            new_window.setWindowTitle(f"{label.device} {label.display_name}")
            self.label_windows[label] = new_window
            new_window.show()

    def shutdown(self):
        """Close app"""
        self.save_view()
        self.MappingThread.shutdown()
        for window in self.label_windows.values():
            if window:
                window.close()
        super().shutdown()
