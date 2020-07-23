import threading

ZOOM = '_zoom'
RADIUS = '_radius'
IMAGE = '_image'
MARK = '_mark'


class MapDataClass:  # TODO Is there a better way of differentiating from the filename? Its causing trouble when trying to use both
    def __init__(self) -> None:
        """

        """
        self.lock = threading.Lock()

        # Map UI attributes
        self.__setattr__(ZOOM, 20)
        self.__setattr__(RADIUS, 0.1)
        self.__setattr__(IMAGE, None)
        self.__setattr__(MARK, None)

    # Get the value of the item from the map by Id
    def getMapValue(self, valueId):
        """

        :param valueId:
        :type valueId:
        :return:
        :rtype:
        """
        with self.lock:
            return self.__getattribute__(valueId)

    # set the value of the item from the map by Id
    # TODO review
    def setMapValue(self, valueId, value) -> None:
        """

        :param valueId:
        :type valueId:
        :param value:
        :type value:
        """
        with self.lock:
            self.__setattr__(valueId, value)
