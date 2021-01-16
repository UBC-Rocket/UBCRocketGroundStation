import queue
from enum import Enum
from threading import RLock
from typing import Dict

from digi.xbee.exception import TimeoutException
from PyQt5 import QtCore

from util.detail import LOGGER
from util.event_stats import Event
from main_window.device_manager import DeviceManager, DeviceType
from main_window.command_parser import CommandParser, CommandType, CommandParsingError
from connections.connection import Connection

COMMAND_SENT_EVENT = Event('command_sent')

class SendThread(QtCore.QThread):

    def __init__(self, connections: Dict[str, Connection], device_manager: DeviceManager, command_parser: CommandParser, parent=None) -> None:
        """Updates GUI, therefore needs to be a QThread and use signals/slots

        :param connections:
        :type connections:
        :param parent:
        :type parent:
        """
        QtCore.QThread.__init__(self, parent)
        self.connections = connections
        self.device_manager = device_manager
        self.command_parser = command_parser

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
        LOGGER.debug("Send thread started")

        # TODO : Once we have multiple connections, we will loop over and send a config request to each
        # Starting up, request hello/ha ndshake/identification
        for connection in self.connections.values():
            try:
                connection.broadcast(self.command_parser.broadcast_data(CommandType.CONFIG))
            except Exception as ex:
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

                try:
                    (device, command, data) = self.command_parser.pase_command(message)
                except CommandParsingError as ex:
                    LOGGER.error(f"Error parsing command: {str(ex)}")
                    continue

                full_address = self.device_manager.get_full_address(device)
                if full_address is None:
                    LOGGER.error(f"Device not yet connected: {device.name}")
                    continue

                connection = self.connections[full_address.connection_name]

                LOGGER.info(f"Sending command {command.name} to device {device.name} ({full_address})")

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
