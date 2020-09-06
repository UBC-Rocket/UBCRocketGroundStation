import collections
import os
import sys

from detail import LOCAL

CR = 0x0D
LF = 0x0A


class StreamLogger:
    def __init__(self, bufstream, size: int) -> None:
        """
        :param bufstream: Buffered stream like a subprocess stdout, that supports read() and peek().
        :type bufstream: Buffered stream
        :param size: Size of in-memory circular log buffer
        :type size: int
        """
        try:
            os.mkdir(os.path.join(LOCAL, ".log"))
        except FileExistsError:
            pass  # directory exists

        if sys.platform == "win32":
            filtered_stream = self._crcrlfFilter(bufstream)
        else:
            filtered_stream = self._noFilter(bufstream)

        self.circularBuffer = collections.deque(maxlen=size)
        self._logged_stream = self._read_and_log(filtered_stream)

    def _read_and_log(self, stream_gen):
        self._logfilePath = os.path.join(LOCAL, ".log", "streamlog")
        with open(self._logfilePath, "wb") as f:
            while True:
                c = next(stream_gen)
                self.circularBuffer.append(c)
                f.write(c)
                f.flush()
                yield c

    def _crcrlfFilter(self, stream):
        while True:
            c = stream.read(1)
            if c == CR and stream.peek(1)[0] == LF:
                yield stream.read(1)  # yields the LF, skipping the CR
            else:
                yield c

    def _noFilter(self, stream):
        while True:
            yield stream.read(1)

    def read(self, number: int):
        """
        :param number: Number of bytes to read
        :type number: int
        :return: Bytes from stream
        :rtype: Iterable of bytes
        """
        data = bytearray()
        for _ in range(number):
            data += next(self._logged_stream)

        return data

    def getHistory(self):
        """
        :return: Contents of circular buffer aka history
        :rtype: Iterable of bytes
        """
        return self.circularBuffer
