import os
import sys
import signal
import multiprocessing
import argparse
import matplotlib
matplotlib.use('QT5Agg') # Ensures that the Qt5 backend is used, otherwise there might be some issues on some OSs (Mac)
from com_window.main import ComWindow
from connections.connection import Connection
from PyQt5 import QtWidgets, QtCore
from profiles.rockets.tantalus import TantalusProfile
from util.self_test import SelfTest
from util.detail import IS_PYINSTALLER, LOGGER

MIN_APP_FONT_POINT_SIZE = 8

def main(qt_args: list[str], self_test: bool = False):
    # Pyinstaller fix https://stackoverflow.com/questions/32672596/pyinstaller-loads-script-multiple-times
    multiprocessing.freeze_support()

    app = QtWidgets.QApplication(qt_args)

    font = app.font()
    font.setPointSize(max(MIN_APP_FONT_POINT_SIZE, font.pointSize()))
    app.setFont(font)

    # TODO: This is kinda hacky
    if IS_PYINSTALLER and '_PYIBoot_SPLASH' in os.environ:
        # Now that we are all loaded, close the splash screen
        try: # pyi_splash is not a real module, its only available if splash was successfully included in the build
            import pyi_splash
            pyi_splash.close()
        except:
            LOGGER.debug("pyi_splash module expected but not found")

    if not self_test:
        # Open com_window dialog to get startup details
        com_window = ComWindow()
        com_window.show()
        return_code = app.exec_()
        if return_code != 0 or com_window.chosen_rocket is None or com_window.chosen_connection is None:
            sys.exit(return_code)

        rocket = com_window.chosen_rocket
        connection = com_window.chosen_connection
        main_window = rocket.construct_app(connection)  # type: ignore

    # TODO: fix typing issue with this.
    else:
        rocket = TantalusProfile()
        connection = rocket.construct_debug_connection()
        main_window = rocket.construct_app(connection)  # type: ignore
        test = SelfTest(main_window)
        test.start()
        
    # Sanity Check if Window is Created
    if not main_window:
        raise Exception("Main Window was not created properly.")

    main_window.show()
    return_code = app.exec_()
    sys.exit(return_code)

if __name__ == "__main__":
    # Enable high DPI if supported
    # TODO: This is a hack, find a better way to do this
    # TAGS: PyQt5
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)  # type: ignore
        
    # Make ctl-c work for closing the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Parse arguments for --self-test
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--self-test", action='store_true')
    args, unparsed_args = parser.parse_known_args()
    # QApplication expects the first argument to be the program name.
    qt_args = sys.argv[:1] + unparsed_args
    
    main(qt_args, self_test = args.self_test)
