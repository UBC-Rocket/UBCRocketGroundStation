import collections
import os
from util.detail import LOGS_DIR, SESSION_ID

A = ord('A')

class ReadFilter:
    def __init__(self, bufstream, size: int) -> None:
        """
        :param bufstream: Buffered stream like a subprocess stdout, that supports read() and peek().
        :type bufstream: Buffered stream
        :param size: Size of in-memory circular log buffer
        :type size: int
        """

        filtered_stream = self._filter(bufstream)

        self.circularBuffer = collections.deque(maxlen=size)
        self._logged_stream = self._read_and_log(filtered_stream)

    def _read_and_log(self, stream_gen):
        self._logfilePath = os.path.join(LOGS_DIR, "streamlog_" + SESSION_ID)
        with open(self._logfilePath, "wb") as f:
            while True:
                c = next(stream_gen)
                self.circularBuffer.append(c)
                f.write(c)
                f.flush()
                yield c

    def _filter(self, stream):
        while True:
            msb = stream.read(1)[0] - A
            lsb = stream.read(1)[0] - A
            yield bytes([(msb << 4) | lsb])

    def read(self, number: int) -> bytes:
        """
        :param number: Number of bytes to read
        :type number: int
        :return: Bytes from stream
        :rtype: Iterable of bytes
        """
        data = bytearray()
        for _ in range(number):
            data += next(self._logged_stream)

        return bytes(data)

    def getHistory(self):
        """
        :return: Contents of circular buffer aka history
        :rtype: Iterable of bytes
        """
        return self.circularBuffer


class WriteFilter:
    def __init__(self, bufstream) -> None:
        """
        :param bufstream: Buffered stream like a subprocess stdout, that supports read() and peek().
        :type bufstream: Buffered stream
        """
        self.stream = bufstream

    def write(self, data: bytes) -> None:
        """
        Write data to buffer.

        Sends each byte in two bytes to reduce ascii range to [A, A + 16). Effectively avoiding all special characters
        that may have varying behavior depending on the OS.

        :param data:
        :type data: bytes
        :return:
        """

        for c in data:
            msb = (c >> 4) + A
            lsb = (c & 0x0F) + A

            self.stream.write(bytes([msb]))
            self.stream.write(bytes([lsb]))

    def flush(self) -> None:
        self.stream.flush()

