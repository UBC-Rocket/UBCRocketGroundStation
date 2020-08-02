import random
import struct
import time
import threading
from array import array

from IConnection import IConnection
from SubpacketIDs import SubpacketEnum


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
            time.sleep(5)
            with self.lock:
                if not self.callback:
                    continue

                bulk_sensor_arr: bytearray = self.bulk_sensor_mock_random()
                # statusPingArr: bytearray = self.statusPingMockSetValues()
                messageArr: bytearray = self.messageValues()
                self.callback(messageArr)

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

    def statusPingMockRandom(self) -> bytearray:
        bulk_sensor_arr: bytearray = bytearray()
        bulk_sensor_arr.append(SubpacketEnum.STATUS_PING.value)  # id
        bulk_sensor_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        bulk_sensor_arr.extend(random.randint(0, 3).to_bytes(length=1, byteorder='big'))  # status1
        bulk_sensor_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        bulk_sensor_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        bulk_sensor_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        bulk_sensor_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        return bulk_sensor_arr

    def statusPingMockSetValues(self) -> bytearray:
        bulk_sensor_arr: bytearray = bytearray()
        bulk_sensor_arr.append(SubpacketEnum.STATUS_PING.value)  # id
        bulk_sensor_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        bulk_sensor_arr.extend((int(2)).to_bytes(length=1, byteorder='big'))  # status1
        # OVERALL_STATUS, BAROMETER, GPS, ACCELEROMETER, IMU, TEMPERATURE
        bulk_sensor_arr.extend((int(252)).to_bytes(length=1, byteorder='big'))  # State of 11111100
        bulk_sensor_arr.extend((int(255)).to_bytes(length=1, byteorder='big'))  # State of 11111111
        # DROGUE_IGNITER_CONTINUITY, MAIN_IGNITER_CONTINUITY, FILE_OPEN_SUCCESS
        bulk_sensor_arr.extend((int(224)).to_bytes(length=1, byteorder='big'))  # State of 11100000
        bulk_sensor_arr.extend((int(255)).to_bytes(length=1, byteorder='big'))  # State of 11111111
        return bulk_sensor_arr

    def messageValues(self) -> bytearray:
        bulk_sensor_arr: bytearray = bytearray()
        bulk_sensor_arr.append(SubpacketEnum.MESSAGE.value)  # id
        bulk_sensor_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        bulk_sensor_arr.extend((int(5)).to_bytes(length=1, byteorder='big'))  # length of the message data
        # bulk_sensor_arr.extend(map(ord, "Hello"))  # message TODO TEST this
        bulk_sensor_arr.extend("Hello".encode('ascii'))  # message TODO TEST this
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
