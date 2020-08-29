import os
import sys
from typing import Union

from detail import LOCAL

from ..connection_factory import ConnectionFactory
from .sim_connection import SimConnection

FIRMWARE_DIR = '../../FW'
EXECUTABLE_NAME = 'program'
FILE_EXTENSION = {
    'win32': '.exe'
}


class SimConnectionFactory(ConnectionFactory):

    def requiresComPort(self) -> bool:
        return False

    def requiresBaudRate(self) -> bool:
        return False

    def construct(self, comPort: Union[int, str, None] = None, baudRate: Union[int, None] = None):
        executableName = EXECUTABLE_NAME

        if sys.platform in FILE_EXTENSION.keys():
            executableName += FILE_EXTENSION[sys.platform]

        return SimConnection(os.path.join(LOCAL, FIRMWARE_DIR), executableName)
