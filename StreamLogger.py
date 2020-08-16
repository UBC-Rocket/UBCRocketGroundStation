import collections
import sys

CR = 0x0D
LF = 0x0A


class StreamLogger:

    def __init__(self, stream, size) -> None:
        """

        :param stream:
        :type stream:
        :param size:
        :type size:
        """
        self.stream = stream
        self.circularBuffer = collections.deque(maxlen=size)

        self.filterCache = bytearray()

    def read(self, number):
        """

        :param number:
        :type number:
        :return:
        :rtype:
        """
        if sys.platform == 'win32':
            data = self._windowsFilter(number)
        else:
            data = self.stream.read(number)

        for b in data:
            self.circularBuffer.append(b)

        return data

    def getHistory(self):
        """

        :return:
        :rtype:
        """
        return list(self.circularBuffer)

    def _readWithCache(self, number):
        """

        :param number:
        :type number:
        :return:
        :rtype:
        """
        data = b''

        numFromCache = min(len(self.filterCache), number)

        data += self.filterCache[0:numFromCache]
        del self.filterCache[0:numFromCache]

        numToRead = number - numFromCache

        if numToRead > 0:
            data += self.stream.read(numToRead)

        return data

    def _windowsFilter(self, number): # TODO: Should probably be in its own class
        """

        :param number:
        :type number:
        :return:
        :rtype:
        """
        data = b''

        while len(data) < number:
            new = self._readWithCache(1)
            if new[0] is CR:
                next = self._readWithCache(1)
                if next[0] is LF:
                    data += next
                else:
                    data += new
                    self.filterCache += next
            else:
                data += new

        return data
