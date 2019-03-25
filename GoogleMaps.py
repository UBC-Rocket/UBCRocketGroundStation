import math
import os

from matplotlib import pyplot as plt
import numpy as np
from urllib.request import urlopen

TILE_SIZE = 256

class MapPoint:

    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude

    def getPixelX(self, zoom):
        return int(math.floor(TILE_SIZE * (0.5 + self.longitude / 360) * math.pow(2,zoom)))

    def getPixelY(self, zoom):
        siny = math.sin(self.latitude * math.pi / 180)

        #Truncating to 0.9999 effectively limits latitude to 89.189. This is
        #about a third of a tile past the edge of the world tile.
        siny = min(max(siny, -0.9999), 0.9999)

        return int(math.floor(TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * math.pow(2, zoom)))

    def getTileX(self,zoom):
        return int(self.getPixelX(zoom)/TILE_SIZE)

    def getTileY(self,zoom):
        return int(self.getPixelY(zoom)/TILE_SIZE)

class MapTile:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def getURL(self):
        return "http://khm3.google.com/kh/v=821&x=%d&y=%d&z=%d" % (self.x, self.y, self.z)

    def getName(self):
        return "x%dy%dz%d" % (self.x, self.y, self.z)

    def getImage(self):
        local = os.path.dirname(os.path.realpath(__file__))
        tiles = os.path.join(local, "tiles")
        impath = os.path.join(tiles, self.getName() + ".png")

        if os.path.isfile(impath):
            return plt.imread(impath)
        else:
            return np.zeros((TILE_SIZE, TILE_SIZE, 3))
            #if not os.path.isdir(tiles):
            #    os.mkdir(tiles)

            #try:
            #    img = plt.imread(urlopen(self.getURL()), format='jpeg')
            #    plt.imsave(impath, img)
            #    return img
            #except:
            #    return np.zeros((TILE_SIZE,TILE_SIZE,3))

def getMapImage(point, zoom, xtiles, ytiles):
    img = None
    for y in range(0, ytiles):
        row = None
        for x in range(0, xtiles):
            t = MapTile(point.getTileX(zoom)-int(xtiles/2)+x, point.getTileY(zoom)-int(ytiles/2)+y, zoom).getImage()[:,:,:3]
            row = appendh(row,t)

        img = appendv(img, row)

    return img

def appendv(A, B):
    if A is None:
        return B
    elif B is None:
        return A
    else:
        return np.vstack((A,B))


def appendh(A, B):
    if A is None:
        return B
    elif B is None:
        return A
    else:
        return np.column_stack((A,B))
