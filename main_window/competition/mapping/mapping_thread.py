import math
import threading
import time
import multiprocessing

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import numpy as np
from PIL import Image

from main_window.data_entry_id import DataEntryIds
from main_window.rocket_data import RocketData
from profiles.rocket_profile import RocketProfile
from . import mapbox_utils
from .map_data import MapData, MapDataValue
from util.detail import LOGGER

# Scaling is linear so a scale factor of 1 means no scaling (aka 1*x=x)
SCALE_FACTOR_NO_SCALE = 1

DEFAULT_RADIUS = 0.1  # Radius in km defining region to be shown in map
DEFAULT_ZOOM = 20  # Scale factor for map tiles


class MappingThread(QtCore.QThread):
    sig_received = pyqtSignal()

    def __init__(self, connection, map_data: MapData, rocket_data: RocketData, rocket_profile: RocketProfile, parent=None) -> None:
        """Mapping work and processing that gets put into MapData, repeatedly as RocketData is updated.
        Signals the main thread to fetch UI elements in MapDataSimilar to ReadData.

        :param connection:
        :type connection:
        :param map_data:
        :type map_data: MapData
        :param rocket_data:
        :type rocket_data:
        :param rocket_profile:
        :type rocket_profile:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.map = map_data
        self.rocket_data = rocket_data

        self.devices = rocket_profile.mapping_devices #List of mappable devices
        self.viewed_devices = self.devices #List of devices currently being viewed

        self._desiredMapSize: tuple(int, int) = None  # Lock in cv is used to protect this
        self.map_zoom = 1
        self._is_shutting_down = False  # Lock in cv is used to protect this

        # Condition variable to watch for notification of new lat and lon
        self.cv = threading.Condition()  # Uses RLock inside when none is provided

        # Must force spawning (as opposed to forking) on unix systems (default / only method supported on Windows) to
        # work around a Python bug. This also makes the behavior between Linux and Windows more similar, which is good
        # for consistency. Must be called before setting up queues.
        # https://bugs.python.org/issue37429, https://bugs.python.org/issue6721 ,https://bugs.python.org/issue40442
        # https://bugs.python.org/issue36533, https://bugs.python.org/issue36533
        multiprocessing.set_start_method('spawn', True)
        # Note: https://docs.python.org/3.7/library/multiprocessing.html#contexts-and-start-methods has a warning saying
        # that spawning processes on Linux with PyInstaller doesn't work. This is a lie... It works... Keep an eye out
        # for issues maybe? Some Github discussions suggest that it may be a more recent fix in PyInstaller.

        # Stitching (and a little bit resizing) the map is a significantly large CPU bound task which was actually
        # blocking all the threads because of Python's GIL. This is resulting in some UI freezing and stuttering.
        # Running the CPU bound tasks in a separate process gets around the GIL problems but introduces some additional
        # IPC complexities (i.e. the queue)
        # Might be able to turn MappingThread into a QProcess so that we dont need both a thread and a process
        self.resultQueue = multiprocessing.Queue()
        self.requestQueue = multiprocessing.Queue()
        self.map_process = multiprocessing.Process(target=processMap, args=(self.requestQueue, self.resultQueue), daemon=True, name="MapProcess")
        self.map_process.start()

        # Must be done last to prevent race condition
        for device in self.viewed_devices:
            self.rocket_data.add_new_callback(device, DataEntryIds.LATITUDE, self.notify)
            self.rocket_data.add_new_callback(device, DataEntryIds.LONGITUDE, self.notify)  # TODO review, could/should be omitted?

    def notify(self) -> None:
        """

        """
        with self.cv:
            self.cv.notify()

    def setViewedDevice(self, devices) -> None:
        """

        :param devices
        :type devices: list of rocket devices
        """
        with self.cv:
            self.viewed_devices = devices
            for device in self.viewed_devices:
                if self.rocket_data.last_value_by_device(device, DataEntryIds.LATITUDE) is None:
                    LOGGER.warning("Data unavailable for {}".format(device.name))

            self.notify()


    def setMapZoom(self, zoom) -> None:
        """

        :param factor
        :type factor: int
        """
        with self.cv:
            self.map_zoom = zoom

    def getMapZoom(self):
        """

        :return:
        :rtype:
        """
        with self.cv:
            return self.map_zoom



    def setDesiredMapSize(self, x, y) -> None:
        """

        :param x:
        :type x:
        :param y:
        :type y:
        """
        with self.cv:
            self._desiredMapSize = (x, y)
            self.notify()

    def getDesiredMapSize(self):
        """

        :return:
        :rtype:
        """
        with self.cv:
            return self._desiredMapSize

    # Draw and show the map on the UI
    def plotMap(self, latitudes, longitudes, radius: float):
        """

        :param latitudes:
        :type latitudes: dict[device, float]
        :param longitudes:
        :type longitudes: dict[device, float]
        :return:
        :rtype:
        """
        if len(latitudes) == 0:
            return False

        #Calculate average of device points
        avg_latitude = sum(latitudes.values())/len(latitudes)
        avg_longitude = sum(longitudes.values()) / len(longitudes)

        #Maximum distance between points and average
        max_lat_diff = max(map(lambda lat: abs(lat - avg_latitude), latitudes.values()))
        max_long_diff = max(map(lambda long: abs(long - avg_longitude), longitudes.values()))

        p0 = mapbox_utils.MapPoint(avg_latitude, avg_longitude)  # Point of interest

        # Create MapPoints that correspond to corners of a square area (of side length 2*radius) surrounding the
        # inputted latitude and longitude. Radius is in km

        lat1 = avg_latitude + (max_lat_diff + radius / 110.574)*self.map_zoom
        lon1 = avg_longitude - (max_long_diff + radius / 111.320 / math.cos(lat1 * math.pi / 180.0))*self.map_zoom
        p1 = mapbox_utils.MapPoint(lat1, lon1)  # Map corner 1

        lat2 = avg_latitude - (max_lat_diff + radius / 110.574)*self.map_zoom
        lon2 = avg_longitude + (max_long_diff + radius / 111.320 / math.cos(lat2 * math.pi / 180.0))*self.map_zoom
        p2 = mapbox_utils.MapPoint(lat2, lon2)  # Map corner 2

        desiredSize = self.getDesiredMapSize()  # x,y
        if not desiredSize:
            return False

        #Find zoom s.t. approximately 2x2 tiles are downloaded
        lon_zoom = math.floor(math.log2(2 / (abs(p1.x - p2.x))))
        lat_zoom = math.floor(math.log2(2 / (abs(p1.y - p2.y))))
        zoom = min(DEFAULT_ZOOM, lat_zoom, lon_zoom)

        self.requestQueue.put_nowait((p0, p1, p2, zoom, desiredSize))

        # NOTE: Passing numpy arrays through any sort of IPC other than plane old shared memory will result in the data
        # being "pickled" and un-"pickled". This uses more processing time than just using shared memory. Since we're
        # not worried about sync safety here, shared memory might be faster... but also harder to implement.
        result = self.resultQueue.get()

        if not result:
            return False

        (resizedMapImage, xMin, xMax, yMin, yMax) = result

        # Update mark coordinates
        marks = [] #list of device locations
        # using latitude keys instead of viewed_devices in case more devices are added before latitudes is updated
        for device in latitudes.keys():
            p = mapbox_utils.MapPoint(latitudes[device], longitudes[device])
            x = (p.x - xMin) / (xMax - xMin)
            y = (p.y - yMin) / (yMax - yMin)
            mark = (x * resizedMapImage.shape[1], y * resizedMapImage.shape[0])
            marks.append(mark)

        map_data_value = MapDataValue(zoom=zoom, radius=radius, image=resizedMapImage, mark=marks)
        self.map.set_map_value(map_data_value)

        return True

    # TODO Info
    def run(self) -> None:
        """

        """
        LOGGER.debug("Mapping thread started")
        last_latitude = None
        last_longitude = None
        last_desired_size = None
        last_map_zoom = None
        last_update_time = 0

        while True:
            with self.cv:
                self.cv.wait()  # CV lock is released while waiting
                if self._is_shutting_down:
                    break

            try:
                # Prevent update spam
                current_time = time.time()
                if current_time - last_update_time < 0.5:
                    time.sleep(0.5)

                # copy location values to use, to keep the values consistent in synchronous but adjacent calls
                latitudes = dict()
                longitudes = dict()

                for device in self.viewed_devices:
                    latitude = self.rocket_data.last_value_by_device(device, DataEntryIds.LATITUDE)
                    longitude = self.rocket_data.last_value_by_device(device, DataEntryIds.LONGITUDE)
                    if latitude and longitude: #plot on map if data not None
                        latitudes[device], longitudes[device] = latitude, longitude

                desired_size = self.getDesiredMapSize()
                map_zoom = self.getMapZoom()

                # Prevent unnecessary work while no location data is received from any device
                if len(latitudes) == 0: #latitudes does not store data if lat = None
                    continue

                # Prevent unnecessary work while data hasnt changed
                if (latitudes, longitudes, desired_size, map_zoom) == (last_latitude, last_longitude, last_desired_size, last_map_zoom):
                    continue

                if self.plotMap(latitudes, longitudes, DEFAULT_RADIUS):
                    # notify UI that new data is available to be displayed
                    self.sig_received.emit()
                else:
                    continue

                last_latitude = latitudes
                last_longitude = longitudes
                last_update_time = current_time
                last_desired_size = desired_size
                last_map_zoom = map_zoom

            except Exception:
                LOGGER.exception("Error in map thread loop")  # Automatically grabs and prints exception info

        LOGGER.warning("Mapping thread shut down")

    def shutdown(self):
        with self.cv:
            if self._is_shutting_down:
                return
            else:
                self._is_shutting_down = True

        self.resultQueue.put(None)

        while self.isRunning():
            with self.cv:
                self.cv.notify()  # Wake up thread

        self.wait()  # join thread

        self.requestQueue.put(None)

        self.resultQueue.cancel_join_thread()
        self.requestQueue.cancel_join_thread()

        self.map_process.join()
        self.map_process.close()
        self.resultQueue.close()
        self.requestQueue.close()


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
    #  process-global constants. Look into file-locks to make this multiprocessing safe. This is an OS feature

    LOGGER.debug("Mapping process started")
    while True:
        try:
            request = requestQueue.get()

            if request is None:  # Shutdown request
                break

            (p0, p1, p2, zoom, desiredSize) = request

            location = mapbox_utils.TileGrid(p1, p2, zoom)
            location.downloadArrayImages()

            largeMapImage = location.genStitchedMap()
            x_min, x_max, y_min, y_max = location.xMin, location.xMax, location.yMin, location.yMax

            if desiredSize is None:
                resizedMapImage = largeMapImage
            else:

                if desiredSize[0]/desiredSize[1] > abs(p1.x - p2.x)/abs(p1.y - p2.y): # Wider aspect ratio
                    x_crop_size = (abs(p1.x - p2.x) * largeMapImage.shape[1]) / (location.xMax - location.xMin)
                    y_crop_size = (x_crop_size * desiredSize[1]) / desiredSize[0]
                else: # Taller aspect ratio
                    y_crop_size = (abs(p1.y - p2.y) * largeMapImage.shape[0]) / (location.yMax - location.yMin)
                    x_crop_size = (y_crop_size * desiredSize[0]) / desiredSize[1]

                center_x = ((p0.x - location.xMin) * largeMapImage.shape[1]) / (location.xMax - location.xMin)
                center_y = ((p0.y - location.yMin) * largeMapImage.shape[0]) / (location.yMax - location.yMin)

                # Crop image centered around p0 (point of interest) and at the desired aspect ratio.
                # Crop is largest possible within rectangle defined by p1 & p2
                x_crop_start = round(center_x - x_crop_size / 2)
                x_crop_end = round(x_crop_start + x_crop_size)
                y_crop_start = round(center_y - y_crop_size / 2)
                y_crop_end = round(y_crop_start + y_crop_size)
                croppedMapImage = largeMapImage[y_crop_start:y_crop_end, x_crop_start:x_crop_end]

                # Check obtained desired aspect ratio (within one pixel)
                assert abs(x_crop_size/y_crop_size - desiredSize[0]/desiredSize[1]) < 1/max(croppedMapImage.shape[0:2])
                assert croppedMapImage.shape[1] == round(x_crop_size)
                assert croppedMapImage.shape[0] == round(y_crop_size)

                x_min, x_max, y_min, y_max = min(p1.x, p2.x), max(p1.x, p2.x), min(p1.y, p2.y), max(p1.y, p2.y)

                if croppedMapImage.shape[1] < desiredSize[0]:
                    # Dont scale up the image. Waste of memory.
                    resizedMapImage = croppedMapImage
                else:
                    # Downsizing the map here to the ideal size for the plot reduces the amount of work required in the
                    # main thread and thus reduces stuttering
                    resizedMapImage = np.array(Image.fromarray(croppedMapImage).resize(
                        (desiredSize[0], desiredSize[1])))  # x,y order is opposite for resize

            resultQueue.put((resizedMapImage, x_min, x_max, y_min, y_max))
        except Exception as ex:
            LOGGER.exception("Exception in processMap process")  # Automatically grabs and prints exception info
            resultQueue.put(None)

    resultQueue.cancel_join_thread()
    requestQueue.cancel_join_thread()
    resultQueue.close()
    requestQueue.close()
    LOGGER.warning("Mapping process shut down")
