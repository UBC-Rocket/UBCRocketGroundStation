import threading
from enum import Enum, auto
from collections import namedtuple

MapDataValue = namedtuple('MapDataValue', ('zoom', 'radius', 'image', 'mark', 'text'))

class MapData:
    def __init__(self) -> None:
        """

        """
        self.lock = threading.Lock()
        self.value: MapDataValue = None

    def get_map_value(self) -> MapDataValue:
        """
        Get the stored value

        :return:
        :rtype:
        """
        with self.lock:
            return self.value

    def set_map_value(self, value: MapDataValue) -> None:
        """
        Set the value

        :param value:
        :type value:
        """
        with self.lock:
            self.value = value

class MapDataSource(Enum):
    SRAD = auto()
    COTS = auto()
