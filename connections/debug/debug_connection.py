import random
import struct
import threading
import time

import connections.debug.radio_packets as radio_packets
from ..connection import Connection
from util.detail import LOGGER
from util.event_stats import Event

ARMED_EVENT = Event('armed')


class DebugConnection(Connection):

    def __init__(self, generate_radio_packets=True) -> None:
        """

        """
        self.lastSend = time.time()  # float seconds
        self.callback = None
        self.lock = threading.RLock()  # Protects callback variable and any other "state" variables
        if generate_radio_packets:
            self.connectionThread = threading.Thread(target=self._run, daemon=True, name="DebugConnectionThread")
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
                full_arr.extend(self.config_mock_set_values())
                full_arr.extend(self.message_values())
                self.send_to_rocket(full_arr)
            time.sleep(2)

    def send_to_rocket(self, data):
        with self.lock:

            if not self.callback:
                raise Exception("Can't send to rocket. No callback set.")

            self.callback(data)

    def bulk_sensor_mock_random(self) -> bytearray:
        """

        :return:
        :rtype: bytearray
        """

        return radio_packets.bulk_sensor(time.time(),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(0, 1e6),
                                         random.uniform(49.260565, 49.263859),
                                         random.uniform(-123.250990, -123.246956),
                                         random.randint(0, 100))

    def status_ping_mock_set_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """

        return radio_packets.status_ping(time.time(),
                                         radio_packets.StatusType.NON_CRITICAL_FAILURE,
                                         0b11111100,
                                         0b11111111,
                                         0b11100000,
                                         0b11111111)

    def message_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """

        return radio_packets.message(time.time(), "hello")

    def config_mock_set_values(self) -> bytearray:
        """

        :return: data_arr
        :rtype: bytearray
        """

        return radio_packets.config(time.time(), True, 0)

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
            if data == b'r':
                ARMED_EVENT.increment()

            LOGGER.info(f"{data} sent to DebugConnection")

    def shutDown(self) -> None:
        pass

    def isIntBigEndian(self) -> bool:
        return True

    def isFloatBigEndian(self) -> bool:
        return True
