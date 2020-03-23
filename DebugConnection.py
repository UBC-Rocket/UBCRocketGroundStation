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

            value = random.uniform(0, 10)

            ba = bytearray(struct.pack("f", value))

            bulk_sensor_arr = self.bulk_sensor_mock_random()
            return bulk_sensor_arr
            # return b"X"+bulk_sensor_arr
        else:
            return None

    def bulk_sensor_mock_random(self):
        bulk_sensor_arr = bytearray()
        bulk_sensor_arr.append(0x30)  # id
        bulk_sensor_arr.extend(random.randint(0, 1e9).to_bytes(length=4, byteorder='big'))  # time
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(struct.pack("f", random.uniform(0, 1e6)))
        bulk_sensor_arr.extend(random.randint(0, 100).to_bytes(length=1, byteorder='big'))  # state
        return bulk_sensor_arr

    def send(self, data):
        pass