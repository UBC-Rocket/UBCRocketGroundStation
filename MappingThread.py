import math
import threading
import time

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

import MapBox

from scipy.misc import imresize

import MapData
from SubpacketIDs import SubpacketEnum


# Mapping work and processing that gets put into MapData, repeatedly as RocketData is updated.
# Signals the main thread to fetch UI elements in MapDataSimilar to ReadData
class MappingThread(QtCore.QThread):
    sig_received = pyqtSignal()
    sig_print = pyqtSignal(str)

    def __init__(self, connection, map: MapData.MapDataClass, data, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.map = map
        self.data = data

        self._desiredMapSize = None  # Tuple(int,int)

        # Condition variable to watch for notification of new lat and lon
        self.cv = threading.Condition()  # Uses RLock inside when none is provided

        # Must be done last to prevent race condition
        self.data.addNewCallback(SubpacketEnum.LATITUDE.value, self.notify)
        self.data.addNewCallback(SubpacketEnum.LONGITUDE.value, self.notify)  # TODO review, could/should be omitted

    def notify(self):
        with self.cv:
            self.cv.notify()

    def setDesiredMapSize(self, x, y):
        with self.cv:
            self._desiredMapSize = (x, y)

    def getDesiredMapSize(self):
        with self.cv:
            return self._desiredMapSize

    # Draw and show the map on the UI
    def plotMap(self, latitude, longitude):
        if longitude is None or latitude is None:
            return

        radius = self.map.getMapValue(MapData.RADIUS)
        zoom = self.map.getMapValue(MapData.ZOOM)

        lat1 = latitude + radius / 110.574
        lon1 = longitude - radius / 111.320 / math.cos(lat1 * math.pi / 180.0)
        p1 = MapBox.MapPoint(lat1, lon1)  # Map corner 1

        lat2 = latitude - radius / 110.574
        lon2 = longitude + radius / 111.320 / math.cos(lat2 * math.pi / 180.0)
        p2 = MapBox.MapPoint(lat2, lon2)  # Map corner 2

        # Create MapPoints that correspond to corners of a square area (of side length 2*radius) surrounding the
        # inputted latitude and longitude.

        location = MapBox.TileGrid(p1, p2, zoom)
        location.downloadArrayImages()

        largeMapImage = location.genStichedMap()

        desiredSize = self.getDesiredMapSize()

        if desiredSize is not None:
            # Scale "to fit", maintains map aspect ratio even if it differs from the desired dimensions aspect ratio
            scaleFactor = min(desiredSize[0] / largeMapImage.shape[0], desiredSize[1] / largeMapImage.shape[1])
        else:
            scaleFactor = 1

        scaleFactor = min(scaleFactor, 1) # You shall not scale the map larger. Waste of memory.

        # Downsizing the map here to the ideal size for the plot reduces the amount of work required in the main
        # thread and thus reduces stuttering
        resizedMapImage = imresize(largeMapImage, (int(scaleFactor * largeMapImage.shape[0]), int(scaleFactor * largeMapImage.shape[1])))

        # Update mark coordinates
        p = MapBox.MapPoint(latitude, longitude)
        x = (p.x - location.xMin) / (location.xMax - location.xMin)
        y = (p.y - location.yMin) / (location.yMax - location.yMin)
        mark = (x * resizedMapImage.shape[0], y * resizedMapImage.shape[1])

        # TODO NOT ROBUST: What if mapdata updated between top of this function and this setMap
        self.map.setMapValue(MapData.IMAGE, resizedMapImage)
        self.map.setMapValue(MapData.LOCATION, location)
        self.map.setMapValue(MapData.MARK, mark)

    # TODO Info
    def run(self):
        last_latitude = None
        last_longitude = None
        last_update_time = 0
        while True:
            with self.cv:
                self.cv.wait()  # CV lock is released while waiting

            try:
                # acquire location to use below here, to keep the values consistent in synchronous but adjacent calls
                latitude = self.data.lastvalue(SubpacketEnum.LATITUDE.value)
                longitude = self.data.lastvalue(SubpacketEnum.LONGITUDE.value)

                # Prevent unnecessary work while no location data is received
                if latitude is None or longitude is None:
                    continue

                # Prevent unnecessary work while data hasnt changed
                if latitude == last_latitude and longitude == last_longitude:
                    continue

                # Prevent update spam from freezing UI
                current_time = time.time()
                if current_time - last_update_time < 0.5:
                    continue

                self.plotMap(latitude, longitude)

                # notify UI that new data is available to be displayed
                self.sig_received.emit()

                last_latitude = latitude
                last_longitude = longitude
                last_update_time = current_time

            except Exception as ex:
                print("Error in map thread loop: %s" % ex)
