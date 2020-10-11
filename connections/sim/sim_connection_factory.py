
import os
import sys
from typing import Union

from detail import LOCAL

from ..connection_factory import ConnectionFactory
from .sim_connection import SimConnection
from .hw_sim import HWSim

FIRMWARE_DIR = "FW"
BUILD_DIR = "FLARE/avionics/build/"
FILE_EXTENSION = {"win32": ".exe"}


class SimConnectionFactory(ConnectionFactory):
    def requiresComPort(self) -> bool:
        return False

    def requiresBaudRate(self) -> bool:
        return False

    def construct(
        self,
        comPort: Union[int, str, None] = None,
        baudRate: Union[int, None] = None,
        rocket=None,
    ):
        assert rocket is not None

        dirs = LOCAL.split("/")
        parent = "/".join(dirs[0:len(dirs) - 1])
        flare = parent + "/" + BUILD_DIR

        # TODO: Make sure build file names always contain needle (works for Tantalus, but wb CoPilot?)
        needle = rocket.rocket_name
        exNames = [s for s in os.listdir(flare) if needle.lower() in s.lower()]
        executableName = "program" if not exNames else exNames[0]

        if sys.platform in FILE_EXTENSION.keys():
            executableName += FILE_EXTENSION[sys.platform]

        return SimConnection(
            flare, executableName, HWSim(rocket.hw_sim_dat)
        )
