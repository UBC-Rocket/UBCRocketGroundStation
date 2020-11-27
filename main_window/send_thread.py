import queue
from enum import Enum
from threading import RLock
from typing import Dict

from digi.xbee.exception import TimeoutException
from PyQt5 import QtCore

from util.detail import LOGGER
from util.event_stats import Event
from main_window.device_manager import DeviceManager, DeviceType
from connections.connection import Connection

COMMAND_SENT_EVENT = Event('command_sent')

# TODO change this section with new Radio protocol comm refactoring
# TODO ASK Are we going to continue to send single characters according to user commands? If yes, then why not
#  provide drop down/multiple select??? AND This should not be here anyway, it relates to communication protocol
#  -> RadioController
class CommandType(Enum):
    ARM = 0x41
    CONFIG = 0x43
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

    def __init__(self, connections: Dict[str, Connection], device_manager: DeviceManager, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connections:
        :type connections:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connections = connections
        self.device_manager = device_manager

        self.commandQueue = queue.Queue()

        self._shutdown_lock = RLock()
        self._is_shutting_down = False

    # TODO Review this data size
    def queueMessage(self, message: str):
        """Function that adds a message to queue for sending.

        :param message:
        :type message:
        """
        self.commandQueue.put_nowait(message)

    # Thread loop that waits for new commands to be queued and sends them when available
    def run(self):
        """

        """

        # TODO : Once we have multiple connections, we will loop over and send a config request to each
        # Starting up, request hello/handshake/identification
        for connection in self.connections.values():
            try:
                connection.broadcast(bytes([CommandType.CONFIG.value]))
            except Exception as ex:
                self.sig_print.emit("Unexpected error while sending config requests!")
                LOGGER.exception("Exception in send thread while sending config requests")

        while True:
            try:
                message = self.commandQueue.get(block=True, timeout=None)  # Block until something new
                self.commandQueue.task_done()

                if message is None:  # Either received None or woken up for shutdown
                    with self._shutdown_lock:
                        if self._is_shutting_down:
                            break
                        else:
                            continue

                message_parts = message.split('.')

                if len(message_parts) != 2:
                    LOGGER.error("Bad command format")
                    continue

                (device_str, command_str) = message_parts

                try:
                    device = DeviceType[device_str.upper()]
                except KeyError:
                    LOGGER.error(f"Unknown device: {device_str}")
                    continue

                full_address = self.device_manager.get_full_address(device)
                if full_address is None:
                    LOGGER.error(f"Device not yet connected: {device.name}")
                    continue

                connection = self.connections[full_address.connection_name]

                try:
                    command = CommandType[command_str.upper()]
                except KeyError:
                    LOGGER.error(f"Unknown command {command_str}")
                    continue

                LOGGER.info(f"Sending command {command.name} to device {device.name} ({full_address})")

                data = bytes([command.value])
                connection.send(full_address.device_address, data)

                LOGGER.info("Sent command!")
                COMMAND_SENT_EVENT.increment()

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
