import os
import sys
import multiprocessing
import argparse
import matplotlib

from mode_select.main import ModeSelect

matplotlib.use('QT5Agg') # Ensures that the Qt5 backend is used, otherwise there might be some issues on some OSs (Mac)
from com_window.main import ComWindow
from download_window.main import DownloadWindow
from PyQt5 import QtWidgets, QtCore
from profiles.rockets.bnb import BNBProfile
from util.self_test import SelfTest
from util.detail import IS_PYINSTALLER, LOGGER

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

MIN_APP_FONT_POINT_SIZE = 8

if __name__ == "__main__":
    # Pyinstaller fix https://stackoverflow.com/questions/32672596/pyinstaller-loads-script-multiple-times
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--self-test", action='store_true')

    args, unparsed_args = parser.parse_known_args()

    # QApplication expects the first argument to be the program name.
    qt_args = sys.argv[:1] + unparsed_args
    app = QtWidgets.QApplication(qt_args)

    font = app.font()
    font.setPointSize(max(MIN_APP_FONT_POINT_SIZE, font.pointSize()))
    app.setFont(font)

    if IS_PYINSTALLER and '_PYIBoot_SPLASH' in os.environ:
        # Now that we are all loaded, close the splash screen
        try: # pyi_splash is not a real module, its only available if splash was successfully included in the build
            import pyi_splash
            pyi_splash.close()
        except:
            LOGGER.debug("pyi_splash module expected but not found")

    if not args.self_test:
        # Open mode select window (tile download or com_window)
        mode_window = ModeSelect()
        mode_window.show()
        return_code = app.exec_()
        if return_code != 0 or mode_window.chosen_window is None:
            sys.exit(return_code)

        if mode_window.chosen_window == "Tile Downloader":
            # Open download_window to download tiles ahead of time
            download_window = DownloadWindow()
            download_window.show()
            return_code = app.exec_()
            # if return_code != 0 or download_window.mode is None:
            if return_code != 0:
                sys.exit(return_code)

        # Open com_window dialog to get startup details
        com_window = ComWindow()
        com_window.show()
        return_code = app.exec_()
        if return_code != 0 or com_window.chosen_rocket is None or com_window.chosen_connection is None:
            sys.exit(return_code)

        rocket = com_window.chosen_rocket
        connection = com_window.chosen_connection
        main_window = rocket.construct_app(connection)

    else:
        rocket = BNBProfile()
        connection = rocket.construct_debug_connection()
        main_window = rocket.construct_app(connection)
        test = SelfTest(main_window)
        test.start()

    main_window.show()
    return_code = app.exec_()
    sys.exit(return_code)
