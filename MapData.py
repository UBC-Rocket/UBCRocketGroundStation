import os
import threading
from enum import Enum

import matplotlib.pyplot as plt
from scipy.misc import imresize

from detail import LOCAL

class MapDataFieldNamesEnum(Enum):
    ZOOM = 'zoom'
    RADIUS = 'radius'
    IMAGE = 'image'
    MARKER_PATH = 'marker path'
    MARKER = 'marker'
    ANNO_BOX = 'annotation box'
    LOCATION = 'location'

class MapData:
    def __init__(self):
        self.lock = threading.Lock()

        # Map UI attributes
        self.mapData = {}
        self.mapData[MapDataFieldNamesEnum.ZOOM.value] = 20
        self.mapData[MapDataFieldNamesEnum.RADIUS.value] = 0.1
        self.mapData[MapDataFieldNamesEnum.IMAGE.value] = None
        self.mapData[MapDataFieldNamesEnum.MARKER_PATH.value] = os.path.join(LOCAL, "marker.png")
        # TODO: imresize removed in latest scipy since it's a duplicate from "Pillow". Update and replace.
        self.mapData[MapDataFieldNamesEnum.MARKER.value] = imresize(plt.imread(self.mapData[MapDataFieldNamesEnum.MARKER_PATH.value]), (12, 12))
        self.mapData[MapDataFieldNamesEnum.ANNO_BOX.value] = None
        self.mapData[MapDataFieldNamesEnum.LOCATION.value] = None

    def getMap(self):
        with self.lock:
            return self.mapData

    # TODO review
    def setMap(self, mapData):
        with self.lock:
            self.mapData = mapData