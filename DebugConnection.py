import random
import struct
import time
import threading

from IConnection import IConnection


class DebugConnection(IConnection):
    def __init__(self):
        self.lastSend = time.time() #float seconds
        self.callback = None
        self.lock = threading.RLock() #Protects callback variable and any other "state" variables
        self.connectionThread = threading.Thread(target=self._run, daemon=True)
        self.connectionThread.start()

    def registerCallback(self, fn):
        with self.lock:
            self.callback = fn

    def _run(self):
        while True:
            time.sleep(1)
            with self.lock:
                if not self.callback:
                    continue
                # accx = random.uniform(0, 1)
                # # L = random.uniform(49.239184, 49.284162) # UBC
                # # l = random.uniform(-123.2766960, -123.210088) # UBC
                # L = random.uniform(49.264940, 49.268063)  # HENN
                # l = random.uniform(-123.255216, -123.249734) # HENN
                #
                # bax = bytearray(struct.pack("f", accx))
                # baL = bytearray(struct.pack("f", L))
                # bal =bytearray(struct.pack("f", l))
                # return b"X"+bax+b"L"+baL+b"l"+bal  # Alex's map mock data?

                bulk_sensor_arr: bytearray = self.bulk_sensor_mock_random()
                self.callback(bulk_sensor_arr)
                # return b"X"+bulk_sensor_arr  # original

    def bulk_sensor_mock_random(self) -> bytearray:
        bulk_sensor_arr: bytearray = bytearray()
        bulk_sensor_arr.append(0x30)  # id
        bulk_sensor_arr.extend((int(time.time())).to_bytes(length=4, byteorder='big'))  # use current integer time
        for x in range(0, 9):
            bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(random.randint(0, 100).to_bytes(length=1, byteorder='big'))  # state
        return bulk_sensor_arr

    def send(self, data):
        with self.lock: #Currently not needed, but good to have for future
            print("%s sent to DebugConnection" % data)