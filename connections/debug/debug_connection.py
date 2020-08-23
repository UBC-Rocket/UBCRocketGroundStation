import random
import struct
import threading
import time

from ..connection import Connection


class DebugConnection(Connection):

    def __init__(self) -> None:
        """

        """
        self.lastSend = time.time()  # float seconds
        self.callback = None
        self.lock = threading.RLock()  # Protects callback variable and any other "state" variables
        self.connectionThread = threading.Thread(target=self._run, daemon=True)
        self.connectionThread.start()

    # Thread loop that creates fake data at constant interval and returns it via callback
    def _run(self) -> None:
        """

        """
        while True:
            time.sleep(1)
            with self.lock:
                if not self.callback:
                    continue

                bulk_sensor_arr: bytearray = self.bulk_sensor_mock_random()
                self.callback(bulk_sensor_arr)

    def bulk_sensor_mock_random(self) -> bytearray:
        """

        :return:
        :rtype: bytearray
        """
        bulk_sensor_arr: bytearray = bytearray()
        bulk_sensor_arr.append(0x30)  # id
        bulk_sensor_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # barometer altitude
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # Acceleration X
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # Acceleration Y
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # Acceleration Z
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # Orientation
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # Orientation
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(0, 1e6)))  # Orientation
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(49.260565, 49.263859)))  # Latitude
        bulk_sensor_arr.extend(struct.pack(">f", random.uniform(-123.250990, -123.246956)))  # Longitude
        bulk_sensor_arr.extend(random.randint(0, 100).to_bytes(length=1, byteorder='big'))  # State
        return bulk_sensor_arr

    # Register callback to which we will send new data
    def registerCallback(self, fn) -> None:
        with self.lock:
            self.callback = fn

    # Send data to connection
    def send(self, data) -> None:
        """

        :param data:
        :type data:
        """
        with self.lock:  # Currently not needed, but good to have for future
            print(f"{data} sent to DebugConnection")

    def shutDown(self) -> None:
        pass

    def isIntBigEndian(self) -> bool:
        return True

    def isFloatBigEndian(self) -> bool:
        return True
