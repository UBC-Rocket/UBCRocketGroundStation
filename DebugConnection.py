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

            return b"X"+bax+b"L"+baL+b"l"+bal
        else:
            return None

    def send(self, data):
        pass