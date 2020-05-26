import math
import threading

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import MapBox

from MapData import MapDataFieldNamesEnum
from SubpacketIDs import SubpacketEnum

# Mapping work and processing that gets put into MapData, repeatedly as RocketData is updated.
# Signals the main thread to fetch UI elements in MapDataSimilar to ReadData
class MappingThread(QtCore.QThread):
    sig_received = pyqtSignal()
    sig_print = pyqtSignal(str)

    def __init__(self, connection, map, data, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.connection = connection
        self.map = map
        self.data = data

        # Condition variable to watch for notification of new lat and lon
        self.cv = threading.Condition()

        self.errored = False  # TODO Review if this is necessary, was used in read/sendThread

    def notify(self):
        with self.cv:
            self.cv.notify()

    # Draw and show the map on the UI
    def plotMap(self, latitude, longitude):
        if longitude is None or latitude is None:
            return

        mapData = self.map.getMap()
        radius = mapData[MapDataFieldNamesEnum.RADIUS.value]
        zoom = mapData[MapDataFieldNamesEnum.ZOOM.value]

        p = MapBox.MapPoint(latitude, longitude) # TODO is this necessary??

        lat1 = latitude + radius / 110.574
        lon1 = longitude - radius / 111.320 / math.cos(lat1 * math.pi / 180.0)
        p1 = MapBox.MapPoint(lat1, lon1)

        lat2 = latitude - radius / 110.574
        lon2 = longitude + radius / 111.320 / math.cos(lat2 * math.pi / 180.0)
        p2 = MapBox.MapPoint(lat2, lon2)

        # Create MapPoints that correspond to corners of a square area (of side length 2*radius) surrounding the
        # inputted latitude and longitude.

        location = MapBox.TileGrid(p1, p2, zoom)
        location.downloadArrayImages()

        mapData[MapDataFieldNamesEnum.IMAGE.value] = location.genStichedMap()
        mapData[MapDataFieldNamesEnum.LOCATION.value] = location
        self.map.setMap(mapData) # TODO NOT ROBUST: What if mapdata updated between top of this function and this setMap


    # Update UI with location on plot
    def updateMark(self, latitude, longitude):
        if longitude is None or latitude is None:
            return

        mapData = self.map.getMap()
        radius = mapData[MapDataFieldNamesEnum.RADIUS.value]
        zoom = mapData[MapDataFieldNamesEnum.ZOOM.value]
        marker = mapData[MapDataFieldNamesEnum.MARKER.value]

        p = MapBox.MapPoint(latitude, longitude)

        lat1 = latitude + radius / 110.574
        lon1 = longitude - radius / 111.320 / math.cos(lat1 * math.pi / 180.0)
        p1 = MapBox.MapPoint(lat1, lon1)

        lat2 = latitude - radius / 110.574
        lon2 = longitude + radius / 111.320 / math.cos(lat2 * math.pi / 180.0)
        p2 = MapBox.MapPoint(lat2, lon2)

        location = MapBox.TileGrid(p1, p2, zoom)

        x = (p.x - location.xMin) / (location.xMax - location.xMin)
        y = (p.y - location.yMin) / (location.yMax - location.yMin)

        mark = (x * MapBox.TILE_SIZE * len(location.ta[0]), y * MapBox.TILE_SIZE * len(location.ta))

        mapData[MapDataFieldNamesEnum.ANNO_BOX.value] = AnnotationBbox(OffsetImage(marker), mark, frameon=False)
        self.map.setMap(mapData) # TODO NOT ROBUST: What if mapdata updated between top of this function and this setMap

    # TODO Info
    def run(self):
        while True:

            with self.cv:
                self.cv.wait()
            try:
                # acquire location to use below here, to keep the values consistent in synchronous but adjacent calls
                latitude = self.data.lastvalue(SubpacketEnum.LATITUDE.value)
                longitude = self.data.lastvalue(SubpacketEnum.LONGITUDE.value)

                self.plotMap(latitude, longitude)
                self.updateMark(latitude, longitude)

                # notify UI that new data is available to be displayed
                self.sig_received.emit()

            except:
                print("Error in map thread loop.")