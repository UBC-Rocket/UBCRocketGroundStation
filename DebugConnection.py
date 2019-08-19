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

            return b"X"+ba
        else:
            return None

    def send(self, data):
        pass