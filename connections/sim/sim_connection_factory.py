import os
import sys
from typing import Union

from detail import LOCAL

from ..connection_factory import ConnectionFactory
from .sim_connection import SimConnection
from .hw_sim import HWSim

FIRMWARE_DIR = "FW"
FILE_EXTENSION = {"win32": ".exe"}


class SimConnectionFactory(ConnectionFactory):
    def requiresComPort(self) -> bool:
        return False

    def requiresBaudRate(self) -> bool:
        return False

    def _getParentDir(self, dir):
        dirs = dir.split("/")
        return "/".join(dirs[0:len(dirs) - 1])

    def construct(
            self,
            comPort: Union[int, str, None] = None,
            baudRate: Union[int, None] = None,
            rocket=None,
    ):
        assert rocket is not None

        # Check FW (child) dir and FLARE (neighbour) dir for rocket build files
        # If multiple build files found throw exception
        flarePath = self._getParentDir(LOCAL) + "/FLARE/avionics/build/"
        neighbourBuildFiles = [s for s in os.listdir(flarePath) if rocket.rocket_name.lower() in s.lower()]

        childBuildFileExists = "program" in os.listdir('./FW')
        neighbourBuildFileExists = bool(neighbourBuildFiles)

        if childBuildFileExists and neighbourBuildFileExists:
            raise Exception(
                f"Multiple build files found: {neighbourBuildFiles[0]} and program")
        elif neighbourBuildFileExists:
            executableName = neighbourBuildFiles[0]
            path = flarePath
        elif childBuildFileExists:
            executableName = "program"
            path = os.path.join(LOCAL, FIRMWARE_DIR)
        else:
            raise Exception(f"No build files found for rocket named {rocket.rocket_name}")

        if sys.platform in FILE_EXTENSION.keys():
            executableName += FILE_EXTENSION[sys.platform]

        return SimConnection(
            path, executableName, HWSim(rocket.hw_sim_dat)
        )
