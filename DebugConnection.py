import random
import struct
import time

from IConnection import IConnection


class DebugConnection(IConnection):
    def __init__(self):
        self.lastSend = time.time() #float seconds


    def get(self):
        currentTime = time.time()

        # TODO: without this, UI gets swamped ("not responding") with updates. Should implement UI updater with rate limiter
        if currentTime - self.lastSend > 1:
            self.lastSend = currentTime

            accx = random.uniform(0, 1)
            # L = random.uniform(49.239184, 49.284162) # UBC
            # l = random.uniform(-123.2766960, -123.210088) # UBC
            L = random.uniform(49.264940, 49.268063)  # HENN
            l = random.uniform(-123.255216, -123.249734) # HENN

            bax = bytearray(struct.pack("f", accx))
            baL = bytearray(struct.pack("f", L))
            bal =bytearray(struct.pack("f", l))

            bulk_sensor_arr: bytearray = self.bulk_sensor_mock_random()
            return bulk_sensor_arr
            # return b"X"+bulk_sensor_arr  # original
            # return b"X"+bax+b"L"+baL+b"l"+bal  # Alex's map mock data? # TODO Discuss how our mocks can coexist
        else:
            return None

    def bulk_sensor_mock_random(self) -> bytearray:
        bulk_sensor_arr: bytearray = bytearray()
        bulk_sensor_arr.append(0x30)  # id
        bulk_sensor_arr.extend(random.randint(0, 1e9).to_bytes(length=4, byteorder='big'))  # time
        for x in range(0, 9):
            bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(random.randint(0, 100).to_bytes(length=1, byteorder='big'))  # state
        return bulk_sensor_arr

    def send(self, data):
        pass