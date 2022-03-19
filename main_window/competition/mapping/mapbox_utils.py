import concurrent.futures
import math
import os
from sys import platform
import time
from typing import Any, Optional

import mapbox
import numpy as np
from matplotlib import pyplot as plt

from util.detail import LOCAL, BUNDLED_DATA, LOGGER

TILE_SIZE = 512

MARKER_PATH = os.path.join(BUNDLED_DATA, "qt_files", "marker.png")

MAPBOX_CACHE = os.path.join(LOCAL, "mapbox_cache")
if not os.path.exists(MAPBOX_CACHE):
    os.mkdir(MAPBOX_CACHE)


def readKey() -> Optional[str]:
    """Reads MapBox API key from apikey.txt.

    :return: API Key for MapBox
    :rtype: Optional[str]
    """
    if os.path.isfile(os.path.join(LOCAL, "apikey.txt")):
        f = open(os.path.join(LOCAL, "apikey.txt"), "r")
        contents = f.read()
        return contents.strip()
    else:
        return None

# Initialize the mapbox map instance
if not (readKey() is None):
    maps = mapbox.Maps(access_token=readKey())
else:
    maps = None

# MacOS specific fix for image downloading
if platform == 'darwin':
    os.environ['NO_PROXY'] = '*'


class MapPoint:
    def __init__(self, latitude: float, longitude: float) -> None:
        """

        :param latitude:
        :type latitude: float
        :param longitude:
        :type longitude: float
        """
        # Values outside this range will produce weird results in the tile calculations
        # Alternative is to normalize angles
        if not -90 < latitude < 90 or not -180 < longitude < 180:
            raise ValueError("Latitude or longitude is out of bounds")

        self.latitude = latitude
        self.longitude = longitude
        self.x = float(0.5 + self.longitude / 360)
        siny = math.sin(self.latitude * math.pi / 180)
        self.y = float((0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.latitude}, {self.longitude}"

    def getPixelX(self, zoom: int) -> int:
        """

        :param zoom:
        :type zoom: int
        :return:
        :rtype: int
        """
        return int(
            math.floor(TILE_SIZE * (0.5 + self.longitude / 360) * math.pow(2, zoom))
        )

    def getPixelY(self, zoom: int) -> int:
        """

        :param zoom:
        :type zoom:
        :return:
        :rtype:
        """
        siny = math.sin(self.latitude * math.pi / 180)

        # Truncating to 0.9999 effectively limits latitude to 89.189. This is
        # about a third of a tile past the edge of the world tile.
        siny = min(max(siny, -0.9999), 0.9999)

        return int(
            math.floor(
                TILE_SIZE
                * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
                * math.pow(2, zoom)
            )
        )

    def getTileX(self, zoom: int) -> int:
        """

        :param zoom:
        :type zoom: int
        :return:
        :rtype: int
        """
        return int(self.getPixelX(zoom) / TILE_SIZE)

    def getTileY(self, zoom: int) -> int:
        """

        :param zoom:
        :type zoom: int
        :return:
        :rtype: int
        """
        return int(self.getPixelY(zoom) / TILE_SIZE)


class MapTile:
    def __init__(self, x: int, y: int, s: int):
        """

        :param x:
        :type x: int
        :param y:
        :type y: int
        :param s:
        :type s: int
        """
        self.x = x
        self.y = y
        self.s = s
        self.is_tile_not_blank = False

    def __str__(self) -> str:
        return f"{self.x}_{self.y}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.x}, {self.y}, {self.s})"

    def __eq__(self, other: Any) -> bool:
        return self.x == other.x and self.y == other.y and self.s == other.s

    def getImage(self, overwrite: bool = False) -> np.ndarray:
        """

        :param overwrite:
        :type overwrite: bool
        :return:
        :rtype: numpy.ndarray
        """
        raw = os.path.join(MAPBOX_CACHE, "raw")
        if not os.path.isdir(raw):
            os.mkdir(raw)
        scalefolder = os.path.join(raw, str(self.s))
        if not os.path.isdir(scalefolder):
            os.mkdir(scalefolder)

        impath = os.path.join(scalefolder, str(self) + ".jpg")

        if ((not os.path.exists(impath)) or overwrite) and not (maps is None):
            response = maps.tile(
                "mapbox.satellite", self.x, self.y, self.s, retina=True
            )
            if response.status_code == 200:
                with open(impath, "wb") as output:
                    output.write(response.content)
                    # LOGGER.debug(f"x: {str(self.x)}, y: {str(self.y)}, s: {str(self.s)}\n")

        if os.path.isfile(impath):
            self.is_tile_not_blank = True
            return plt.imread(impath, "jpeg")
        else:
            return np.zeros((TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8) # np generates float by default, pillow doesnt support that

    def imageExists(self) -> bool:
        """

        :return:
        :rtype: bool
        """
        return os.path.isfile(
            os.path.join(MAPBOX_CACHE, "raw", str(self.s), str(self) + ".png")
        )


class TileGrid:
    def __init__(self, p1: MapPoint, p2: MapPoint, s: int):
        """

        :param p1:
        :type p1: MapPoint
        :param p2:
        :type p2: MapPoint
        :param s:
        :type s: int
        """
        self.p1 = p1
        self.p2 = p2
        self.scale = min(s, 18)
        self.ta = []
        self.xMin = None
        self.xMax = None
        self.yMin = None
        self.yMax = None
        self.tile_x_min = None
        self.tile_x_max = None
        self.tile_y_min = None
        self.tile_y_max = None
        self.width = None
        self.height = None
        self.genTileArray()
        if self.width > 5 or self.height > 5:
            LOGGER.warning(f"Large map ({self.width}x{self.height} tiles)")

    def __str__(self) -> str:
        return f"{self.scale}_{self.tile_x_min}-{self.tile_x_max}_{self.tile_y_min}-{self.tile_y_max}"

    def genTileArray(self) -> None:
        """

        """
        t1 = pointToTile(self.p1, self.scale)
        t2 = pointToTile(self.p2, self.scale)
        self.tile_x_min = min(t1.x, t2.x)
        self.tile_x_max = max(t1.x, t2.x)
        self.tile_y_min = min(t1.y, t2.y)
        self.tile_y_max = max(t1.y, t2.y)

        self.xMin = self.tile_x_min / pow(2, self.scale)
        self.xMax = (self.tile_x_max + 1) / pow(2, self.scale)
        self.yMin = self.tile_y_min / pow(2, self.scale)
        self.yMax = (self.tile_y_max + 1) / pow(2, self.scale)
        # LOGGER.debug(str(self.xMin) + "  " + str(self.xMax) + "  " + str(self.yMin) + "  " + str(self.yMax))

        ta = []

        for i in range(self.tile_y_min, self.tile_y_max + 1):
            row = []
            for j in range(self.tile_x_min, self.tile_x_max + 1):
                row.append(MapTile(j, i, self.scale))
            ta.append(row)
        self.ta = ta

        self.width = len(self.ta[0])
        self.height = len(self.ta)

    def downloadArrayImages(self, attempts: int = 3, overwrite: bool = False) -> None:
        """

        :param attempts:
        :type attempts: int
        :param overwrite:
        :type overwrite: bool
        """
        LOGGER.debug(f"Beginning download of size {str(self.scale)} tiles.")
        t1 = time.perf_counter()

        def getRow(row):
            for i in row:
                a = attempts
                while (not i.imageExists()) and (a > 0):
                    i.getImage(overwrite=overwrite)
                    a = a - 1

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(getRow, self.ta)
        t2 = time.perf_counter()
        LOGGER.debug(f"Successfully downloaded size {str(self.scale)} tiles in {t2 - t1} seconds.")

    def genStitchedMap(self, overwrite: bool = False) -> np.ndarray:
        """

        :param overwrite:
        :type overwrite: bool
        :return:
        :rtype: numpy.ndarray
        """

        def appendv(A, B):
            if A is None:
                return B
            elif B is None:
                return A
            else:
                return np.vstack((A, B))

        def appendh(A, B):
            if A is None:
                return B
            elif B is None:
                return A
            else:
                return np.column_stack((A, B))

        out = os.path.join(MAPBOX_CACHE, "out")
        if not os.path.isdir(out):
            os.mkdir(out)

        outfile = os.path.join(out, f"output_{str(self)}.png")

        if (not os.path.isfile(outfile)) or overwrite:
            LOGGER.debug(f"Generating size {str(self.scale)} map!")

            t1 = time.perf_counter()

            is_img_not_blank = False
            img = None
            for i in self.ta:
                row = None
                for j in i:
                    row = appendh(row, j.getImage())
                    if j.is_tile_not_blank is True:
                        is_img_not_blank = True

                img = appendv(img, row)

            if is_img_not_blank is True:
                plt.imsave(outfile, img)

            t2 = time.perf_counter()
            LOGGER.debug(f"Successfully generated size {str(self.scale)} map in {t2 - t1} seconds.")
            return img
        else:
            LOGGER.debug(f"Found size {str(self.scale)} map!")
            return plt.imread(outfile, "jpeg")


def pointToTile(p: MapPoint, s: int) -> MapTile:
    """

    :param p:
    :type p: MapPoint
    :param s:
    :type s: int
    :return:
    :rtype: MapTile
    """
    return MapTile(math.floor(p.x * 2.0 ** s), math.floor(p.y * 2.0 ** s), s)
