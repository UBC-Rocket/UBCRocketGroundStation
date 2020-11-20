import queue
from enum import Enum
from threading import RLock

from digi.xbee.exception import TimeoutException
from PyQt5 import QtCore

from util.detail import LOGGER


# TODO change this section with new Radio protocol comm refactoring
# TODO ASK Are we going to continue to send single characters according to user commands? If yes, then why not
#  provide drop down/multiple select??? AND This should not be here anyway, it relates to communication protocol
#  -> RadioController
class CommandType(Enum):
    ARM = 0x41
    DISARM = 0x44
    PING = 0x50
    BULK = 0x30
    ACCELX = 0x10
    ACCELY = 0x11
    ACCELZ = 0x12
    BAROPRES = 0x13
    BAROTEMP = 0x14
    TEMP = 0x15
    LAT = 0x19
    LON = 0x1A
    GPSALT = 0x1B
    ALT = 0x1C
    STATE = 0x1D
    VOLT = 0x1E
    GROUND = 0x1F
    GPS = 0x04
    ORIENT = 0x06


class SendThread(QtCore.QThread):

    def __init__(self, connection, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connection:
        :type connection:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connection = connection

        self.commandQueue = queue.Queue()

        self._shutdown_lock = RLock()
        self._is_shutting_down = False

    # TODO Review this data size
    def queueMessage(self, word):
        """Function that adds a message of size 'word' to queue for sending.

        :param word:
        :type word:
        """
        self.commandQueue.put_nowait(word)

    # Thread loop that waits for new commands to be queued and sends them when available
    def run(self):
        """

        """
        while True:
            try:
                word = self.commandQueue.get(block=True, timeout=None)  # Block until something new
                self.commandQueue.task_done()

                if word is None:  # Either received None or woken up for shutdown
                    with self._shutdown_lock:
                        if self._is_shutting_down:
                            break
                        else:
                            continue

                try:
                    command = CommandType[word.upper()]
                    data = bytes([command.value])
                except KeyError:
                    LOGGER.error("Unknown Command")
                    continue

                self.connection.send(data)

                LOGGER.info("Sent command!")

            except TimeoutException:  # TODO: Connection should have converted this to a generic exception for decoupling
                LOGGER.error("Message timed-out!")

            except queue.Empty:
                pass

            except Exception as ex:
                LOGGER.exception("Unexpected error while sending!")  # Automatically grabs and prints exception info

        LOGGER.warning("Send thread shut down")

    def shutdown(self):
        with self._shutdown_lock:
            self._is_shutting_down = True
        self.commandQueue.put(None)  # Wake up thread
        self.wait()  # join thread
