import random
import struct
import time
import threading

from IConnection import IConnection


class DebugConnection(IConnection):
    def __init__(self):
        self.lastSend = time.time()  # float seconds
        self.callback = None
        self.lock = threading.RLock()  # Protects callback variable and any other "state" variables
        self.connectionThread = threading.Thread(target=self._run, daemon=True)
        self.connectionThread.start()

    # Register callback to which we will send new data
    def registerCallback(self, fn):
        with self.lock:
            self.callback = fn

    # Thread loop that creates fake data at constant interval and returns it via callback
    def _run(self):
        while True:
            time.sleep(1)
            with self.lock:
                if not self.callback:
                    continue

                bulk_sensor_arr: bytearray = self.bulk_sensor_mock_random()
                self.callback(bulk_sensor_arr)

    def bulk_sensor_mock_random(self) -> bytearray:
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

    # Send data to connection
    def send(self, data):
        with self.lock:  # Currently not needed, but good to have for future
            print("%s sent to DebugConnection" % data)

    def isIntBigEndian(self):
        return True

    def isFloatBigEndian(self):
        return True

    def shutDown(self):
        pass
