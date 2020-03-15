import math
import os
import random
import sys

import threading
import concurrent.futures
import time

from matplotlib import pyplot as plt
import numpy as np

import mapbox

if getattr(sys, 'frozen', False):
    local = os.path.dirname(sys.executable)
elif __file__:
    local = os.path.dirname(__file__)

TILE_SIZE = 512


def readKey():
    if os.path.isfile(os.path.join(local, "apikey.txt")):
        f = open(os.path.join(local, "apikey.txt"), "r")
        contents = f.read()
        return contents.strip()
    else:
        return None


if not (readKey() is None):
    maps = mapbox.Maps(access_token=readKey())
else:
    maps = None


class MapPoint:

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
        self.x = float(0.5 + self.longitude / 360)
        siny = math.sin(self.latitude * math.pi / 180)
        self.y = float((0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)))

    def getPixelX(self, zoom):
        return int(math.floor(TILE_SIZE * (0.5 + self.longitude / 360) * math.pow(2, zoom)))

    def getPixelY(self, zoom):
        siny = math.sin(self.latitude * math.pi / 180)

        # Truncating to 0.9999 effectively limits latitude to 89.189. This is
        # about a third of a tile past the edge of the world tile.
        siny = min(max(siny, -0.9999), 0.9999)

        return int(
            math.floor(TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * math.pow(2, zoom)))

    def getTileX(self, zoom):
        return int(self.getPixelX(zoom) / TILE_SIZE)

    def getTileY(self, zoom):
        return int(self.getPixelY(zoom) / TILE_SIZE)


## MapPoint Examples:
p1 = MapPoint(49.284162, -123.2766960)  # NW of UBC
p2 = MapPoint(49.239184, -123.210088)  # SE of UBC
p3 = MapPoint(49.266063, -123.261348)  # NW of Vanier
p4 = MapPoint(49.262715, -123.255472)  # SE of Vanier


class MapTile:

    def __init__(self, x, y, s):
        self.x = x
        self.y = y
        self.s = s

    def getName(self):
        return f"{self.x}_{self.y}"

    def getImage(self, overwrite=False):

        raw = os.path.join(local, "raw")
        if not os.path.isdir(raw):
            os.mkdir(raw)
        scalefolder = os.path.join(raw, str(self.s))
        if not os.path.isdir(scalefolder):
            os.mkdir(scalefolder)

        impath = os.path.join(scalefolder, self.getName() + ".jpg")

        if ((not os.path.exists(impath)) or overwrite) and not (maps is None):
            response = maps.tile("mapbox.satellite", self.x, self.y, self.s, retina=True)
            if response.status_code == 200:
                with open(impath, "wb") as output:
                    output.write(response.content)
                    # print(f"x: {str(self.x)}, y: {str(self.y)}, s: {str(self.s)}\n")

        if os.path.isfile(impath):
            return plt.imread(impath, 'jpeg')
        else:
            return np.zeros((TILE_SIZE, TILE_SIZE, 3))

    def imageExists(self):
        return os.path.isfile(os.path.join(local, "raw", str(self.s), self.getName() + ".png"))


class TileGrid:

    def __init__(self, p1, p2, s):
        self.p1 = p1
        self.p2 = p2
        self.scale = min(s, 18)
        self.ta = []
        self.xMin = None
        self.xMax = None
        self.yMin = None
        self.yMax = None
        self.width = None
        self.height = None
        self.genTileArray()

    def genTileArray(self):
        t1 = pointToTile(self.p1, self.scale)
        t2 = pointToTile(self.p2, self.scale)
        x1 = min(t1.x, t2.x)
        x2 = max(t1.x, t2.x)
        y1 = min(t1.y, t2.y)
        y2 = max(t1.y, t2.y)

        self.xMin = x1 / pow(2, self.scale)
        self.xMax = (x2 + 1) / pow(2, self.scale)
        self.yMin = y1 / pow(2, self.scale)
        self.yMax = (y2 + 1) / pow(2, self.scale)
        # print(str(self.xMin) + "  " + str(self.xMax) + "  " + str(self.yMin) + "  " + str(self.yMax))

        ta = []

        for i in range(y1, y2 + 1):
            row = []
            for j in range(x1, x2 + 1):
                row.append(MapTile(j, i, self.scale))
            ta.append(row)
        self.ta = ta

        self.width = len(self.ta[0])
        self.height = len(self.ta)

    def downloadArrayImages(self, attempts=3, overwrite=False):
        print(f"Beginning download of size {str(self.scale)} tiles.")
        t1 = time.perf_counter()

        def getRow(row):
            for i in row:
                a = attempts
                while (not i.imageExists()) and (a > 0):
                    i.getImage(overwrite=overwrite)
                    a = a - 1

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(getRow, self.ta)
            executor.shutdown()
        t2 = time.perf_counter()
        print(f"Successfully downloaded size {str(self.scale)} tiles in {t2 - t1} seconds.")

    def genStichedMap(self, overwrite=False):
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

        out = os.path.join(local, "out")
        if not os.path.isdir(out):
            os.mkdir(out)

        outfile = os.path.join(out,
                               f"output_{str(min(self.p1.x, self.p2.x))}-{str(max(self.p1.x, self.p2.x))}_{str(min(self.p1.y, self.p2.y))}-{str(max(self.p1.y, self.p2.y))}_{str(self.scale)}.png")
        if (not os.path.isfile(outfile)) or overwrite == True:
            print(f"Generating size {str(self.scale)} map!")

            t1 = time.perf_counter()

            img = None
            for i in self.ta:
                row = None
                for j in i:
                    row = appendh(row, j.getImage())

                img = appendv(img, row)

            plt.imsave(outfile, img)
            t2 = time.perf_counter()
            print(f"Successfully generated size {str(self.scale)} map in {t2 - t1} seconds.")
            return img
        else:
            print(f"Found size {str(self.scale)} map!")
            return plt.imread(outfile, 'jpeg')


def pointToTile(p, s):
    return MapTile(math.floor(p.x * 2.0 ** s), math.floor(p.y * 2.0 ** s), s)


## TileGrid Examples
tg = TileGrid(p1, p2, 16)
tg2 = TileGrid(p3, p4, 18)
