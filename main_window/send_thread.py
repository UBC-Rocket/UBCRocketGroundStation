import queue

from digi.xbee.exception import TimeoutException, XBeeException
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

from util.detail import LOGGER

# TODO change this section with new Radio protocol comm refactoring
COM_ID = {
    # TODO ASK Are we going to continue to send single characters according to user commands? If yes, then why not
    #  provide drop down/multiple select??? AND This should not be here anyway, it relates to communication protocol
    #  -> RadioController
    "arm": 'r',
    "cameras on": 'C',
    "cameras off": 'O',
    "halo": 'H',
    "satcom": 's',
    "reset": 'R',
    "status": 'S',
    "main": 'm',
    "drogue": 'd',
    "ping": 'p'
}


class SendThread(QtCore.QThread):
    sig_print = pyqtSignal(str)

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

        self.errored = False

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

                # Checks to see if one of pre-configed cmds. If it is, then it just sends the char associated with cmd
                bytes = None
                if word in COM_ID:
                    bytes = COM_ID[word].encode('ascii')

                else:
                    bytes = word.encode('ascii')

                self.connection.send(bytes)

                self.sig_print.emit("Sent!")

            except TimeoutException:
                self.sig_print.emit("Message timed-out!")

            except queue.Empty:
                pass

            except Exception as ex:
                self.sig_print.emit("Unexpected error while sending!")
                LOGGER.exception("Exception in send thread") # Automatically grabs and prints exception info
