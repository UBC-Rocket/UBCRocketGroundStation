import random
import struct
import threading
import time

from ..connection import Connection
from main_window.subpacket_ids import SubpacketEnum


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
            with self.lock:
                if not self.callback:
                    continue

                full_arr: bytearray = bytearray()
                full_arr.extend(self.bulk_sensor_mock_random())
                full_arr.extend(self.status_ping_mock_set_values())
                full_arr.extend(self.message_values())
                self.callback(full_arr)
            time.sleep(2)

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

    def status_ping_mock_random(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """
        data_arr: bytearray = bytearray()
        data_arr.append(SubpacketEnum.STATUS_PING.value)  # id
        data_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        data_arr.extend(random.randint(0, 3).to_bytes(length=1, byteorder='big'))  # status1
        data_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        data_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        data_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        data_arr.extend(random.randint(0, 255).to_bytes(length=1, byteorder='big'))  # State
        return data_arr

    def status_ping_mock_set_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """
        data_arr: bytearray = bytearray()
        data_arr.append(SubpacketEnum.STATUS_PING.value)  # id
        data_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        data_arr.extend((int(2)).to_bytes(length=1, byteorder='big'))  # status1
        # OVERALL_STATUS, BAROMETER, GPS, ACCELEROMETER, IMU, TEMPERATURE
        data_arr.extend((int(252)).to_bytes(length=1, byteorder='big'))  # State of 11111100
        data_arr.extend((int(255)).to_bytes(length=1, byteorder='big'))  # State of 11111111
        # DROGUE_IGNITER_CONTINUITY, MAIN_IGNITER_CONTINUITY, FILE_OPEN_SUCCESS
        data_arr.extend((int(224)).to_bytes(length=1, byteorder='big'))  # State of 11100000
        data_arr.extend((int(255)).to_bytes(length=1, byteorder='big'))  # State of 11111111
        return data_arr

    def message_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """
        data_arr: bytearray = bytearray()
        data_arr.append(SubpacketEnum.MESSAGE.value)  # id
        data_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        data_arr.extend((int(5)).to_bytes(length=1, byteorder='big'))  # length of the message data
        data_arr.extend([ord(ch) for ch in 'hello'])  # message
        return data_arr

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
