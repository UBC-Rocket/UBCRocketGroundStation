import threading

ZOOM = '_zoom'
RADIUS = '_radius'
IMAGE = '_image'
MARK = '_mark'


class MapData:
    def __init__(self) -> None:
        """

        """
        self.lock = threading.Lock()

        # Map UI attributes
        setattr(self, ZOOM, 20)
        setattr(self, RADIUS, 0.1)
        setattr(self, IMAGE, None)
        setattr(self, MARK, None)

    # Get the value of the item from the map by Id
    def getMapValue(self, valueId):
        """

        :param valueId:
        :type valueId:
        :return:
        :rtype:
        """
        with self.lock:
            return getattr(self, valueId)

    # set the value of the item from the map by Id
    def setMapValue(self, valueId, value) -> None:
        """

        :param valueId:
        :type valueId:
        :param value:
        :type value:
        """
        with self.lock:
            setattr(self, valueId, value)
