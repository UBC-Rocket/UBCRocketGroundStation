import math
import threading
import time
from multiprocessing import Process, Queue

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import numpy as np
from PIL import Image

from main_window.subpacket_ids import SubpacketEnum
from main_window.rocket_data import RocketData
from profiles.rocket_profile import RocketProfile
from . import map_data, mapbox_utils
from util.detail import LOGGER

# Scaling is linear so a scale factor of 1 means no scaling (aka 1*x=x)
SCALE_FACTOR_NO_SCALE = 1


class MappingThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connection, m: map_data.MapData, rocket_data: RocketData, rocket_profile: RocketProfile, parent=None) -> None:
        """Mapping work and processing that gets put into MapData, repeatedly as RocketData is updated.
        Signals the main thread to fetch UI elements in MapDataSimilar to ReadData.

        :param connection:
        :type connection:
        :param map:
        :type map: map_data.MapData
        :param rocket_data:
        :type rocket_data:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.map = m
        self.rocket_data = rocket_data

        self.device = rocket_profile.mapping_device

        self._desiredMapSize: tuple(int, int) = None  # Lock in cv is used to protect this
        self._is_shutting_down = False  # Lock in cv is used to protect this

        # Condition variable to watch for notification of new lat and lon
        self.cv = threading.Condition()  # Uses RLock inside when none is provided

        # Stitching (and a little bit resizing) the map is a significantly large CPU bound task which was actually
        # blocking all the threads because of Python's GIL. This is resulting in some UI freezing and stuttering.
        # Running the CPU bound tasks in a separate process gets around the GIL problems but introduces some additional
        # IPC complexities (i.e. the queue)
        # Might be able to turn MappingThread into a QProcess so that we dont need both a thread and a process
        self.resultQueue = Queue(1)
        self.requestQueue = Queue(1)
        mapProc = Process(target=processMap, args=(self.requestQueue, self.resultQueue), daemon=True, name="MapProcess")
        mapProc.start()

        # Must be done last to prevent race condition
        self.rocket_data.addNewCallback(self.device, SubpacketEnum.LATITUDE.value, self.notify)
        self.rocket_data.addNewCallback(self.device, SubpacketEnum.LONGITUDE.value, self.notify)  # TODO review, could/should be omitted

    def notify(self) -> None:
        """

        """
        with self.cv:
            self.cv.notify()

    def setDesiredMapSize(self, x, y) -> None:
        """

        :param x:
        :type x:
        :param y:
        :type y:
        """
        with self.cv:
            self._desiredMapSize = (x, y)

    def getDesiredMapSize(self):
        """

        :return:
        :rtype:
        """
        with self.cv:
            return self._desiredMapSize

    # Draw and show the map on the UI
    def plotMap(self, latitude: float, longitude: float):
        """

        :param latitude:
        :type latitude: float
        :param longitude:
        :type longitude: float
        :return:
        :rtype:
        """
        if longitude is None or latitude is None:
            return False

        radius = self.map.getMapValue(map_data.RADIUS)
        zoom = self.map.getMapValue(map_data.ZOOM)

        # Create MapPoints that correspond to corners of a square area (of side length 2*radius) surrounding the
        # inputted latitude and longitude.

        lat1 = latitude + radius / 110.574
        lon1 = longitude - radius / 111.320 / math.cos(lat1 * math.pi / 180.0)
        p1 = mapbox_utils.MapPoint(lat1, lon1)  # Map corner 1

        lat2 = latitude - radius / 110.574
        lon2 = longitude + radius / 111.320 / math.cos(lat2 * math.pi / 180.0)
        p2 = mapbox_utils.MapPoint(lat2, lon2)  # Map corner 2

        desiredSize = self.getDesiredMapSize()

        self.requestQueue.put_nowait((p1, p2, zoom, desiredSize))

        # NOTE: Passing numpy arrays through any sort of IPC other than plane old shared memory will result in the data
        # being "pickled" and un-"pickled". This uses more processing time than just using shared memory. Since we're
        # not worried about sync safety here, shared memory might be faster... but also harder to implement.
        result = self.resultQueue.get()

        if not result:
            return False

        (resizedMapImage, xMin, xMax, yMin, yMax) = result

        # Update mark coordinates
        p = mapbox_utils.MapPoint(latitude, longitude)
        x = (p.x - xMin) / (xMax - xMin)
        y = (p.y - yMin) / (yMax - yMin)
        mark = (x * resizedMapImage.shape[0], y * resizedMapImage.shape[1])

        # TODO NOT ROBUST: What if mapdata updated between top of this function and this setMap
        self.map.setMapValue(map_data.IMAGE, resizedMapImage)
        self.map.setMapValue(map_data.MARK, mark)

        return True

    # TODO Info
    def run(self) -> None:
        """

        """
        last_latitude = None
        last_longitude = None
        last_update_time = 0
        while True:
            with self.cv:
                self.cv.wait()  # CV lock is released while waiting
                if self._is_shutting_down:
                    break

            try:
                # acquire location to use below here, to keep the values consistent in synchronous but adjacent calls
                latitude = self.rocket_data.last_value_by_device(self.device, SubpacketEnum.LATITUDE.value)
                longitude = self.rocket_data.last_value_by_device(self.device, SubpacketEnum.LONGITUDE.value)

                # Prevent unnecessary work while no location data is received
                if latitude is None or longitude is None:
                    continue

                # Prevent unnecessary work while data hasnt changed
                if latitude == last_latitude and longitude == last_longitude:
                    continue

                # Prevent update spam
                current_time = time.time()
                if current_time - last_update_time < 0.5:
                    continue

                if self.plotMap(latitude, longitude):
                    # notify UI that new data is available to be displayed
                    self.sig_received.emit()
                else:
                    continue

                last_latitude = latitude
                last_longitude = longitude
                last_update_time = current_time

            except Exception:
                LOGGER.exception("Error in map thread loop")  # Automatically grabs and prints exception info

        LOGGER.warning("Mapping thread shut down")

    def shutdown(self):
        with self.cv:
            self._is_shutting_down = True

        while self.isRunning():
            with self.cv:
                self.cv.notify()  # Wake up thread

        self.wait()  # join thread


def processMap(requestQueue, resultQueue):
    """To be run in a new process as the stitching and resizing is a CPU bound task

    :param requestQueue:
    :type requestQueue: Queue
    :param resultQueue:
    :type resultQueue: Queue
    """

    # On Windows, process forking does not copy globals and thus all packeges are re-imported. Not for threads
    # though.
    # Note: This means that on Windows the logger will create one log file per process because the session ID
    # is based on the import time
    # https://docs.python.org/3/library/multiprocessing.html#logging
    # TODO: Fix by creating .session file which contains session ID and other
    #  process-global constants. Look into file-locks to make this multiprocessing saft. This is an OS feature

    while True:
        try:
            (p1, p2, zoom, desiredSize) = requestQueue.get()

            location = mapbox_utils.TileGrid(p1, p2, zoom)
            location.downloadArrayImages()

            largeMapImage = location.genStitchedMap()

            if desiredSize is not None:
                # Scale "to fit", maintains map aspect ratio even if it differs from the desired dimensions aspect ratio
                scaleFactor = min(desiredSize[0] / largeMapImage.shape[0], desiredSize[1] / largeMapImage.shape[1])
            else:
                scaleFactor = SCALE_FACTOR_NO_SCALE

            scaleFactor = min(scaleFactor,
                              SCALE_FACTOR_NO_SCALE)  # You shall not scale the map larger. Waste of memory.

            # Downsizing the map here to the ideal size for the plot reduces the amount of work required in the main
            # thread and thus reduces stuttering
            resizedMapImage = np.array(Image.fromarray(largeMapImage).resize(
                (int(scaleFactor * largeMapImage.shape[0]), int(scaleFactor * largeMapImage.shape[1]))))

            resultQueue.put((resizedMapImage, location.xMin, location.xMax, location.yMin, location.yMax))
        except Exception as ex:
            LOGGER.exception("Exception in processMap process")  # Automatically grabs and prints exception info
            resultQueue.put(None)
