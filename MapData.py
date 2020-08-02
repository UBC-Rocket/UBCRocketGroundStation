import threading


ZOOM = '_zoom'
RADIUS = '_radius'
IMAGE = '_image'
MARK = '_mark'
LOCATION = '_location'


class MapData:
    def __init__(self):
        self.lock = threading.Lock()

        # Map UI attributes
        self.__setattr__(ZOOM, 20)
        self.__setattr__(RADIUS, 0.1)
        self.__setattr__(IMAGE, None)
        self.__setattr__(MARK, None)
        self.__setattr__(LOCATION, None)

    # Get the value of the item from the map by Id
    def getMapValue(self, valueId):
        with self.lock:
            return self.__getattribute__(valueId)

    # set the value of the item from the map by Id
    # TODO review
    def setMapValue(self, valueId, value):
        with self.lock:
            self.__setattr__(valueId, value)
