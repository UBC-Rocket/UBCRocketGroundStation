import os
import sys
from typing import Union

from util.detail import LOCAL, LOGGER

from ..connection_factory import ConnectionFactory
from .sim_connection import SimConnection
from pathlib import Path

FLARE_PATH = os.path.join(Path(LOCAL).parent, 'FLARE', 'avionics', 'build')

LOCAL_PATH = os.path.join(LOCAL, 'FW')

FILE_EXTENSION = {
    'linux': '',
    'win32': '.exe',
    'darwin': ''
}

LOCAL_NAME = 'program' + FILE_EXTENSION[sys.platform]


class SimConnectionFactory(ConnectionFactory):

    @property
    def connection_name(self) -> str:
        return "SIM"

    @property
    def requires_com_port(self) -> bool:
        return False

    @property
    def requires_baud_rate(self) -> bool:
        return False

    def construct(
            self,
            comPort: Union[int, str, None] = None,
            baudRate: Union[int, None] = None,
            rocket=None,
    ):
        assert rocket is not None

        if rocket.sim_executable_name is None:
            raise Exception("No sim executable name defined for this rocket profile")

        # Check FW (child) dir and FLARE (neighbour) dir for rocket build files
        # If multiple build files found throw exception
        neighbourBuildFile = rocket.sim_executable_name + FILE_EXTENSION[sys.platform]
        neighbourBuildFileExists = os.path.exists(os.path.join(FLARE_PATH, neighbourBuildFile))

        childBuildFileExists = os.path.exists(os.path.join(LOCAL_PATH, LOCAL_NAME))

        if childBuildFileExists and neighbourBuildFileExists:
            raise FirmwareNotFound(
                f"Multiple build files found: {neighbourBuildFile} and {LOCAL_NAME}")
        elif neighbourBuildFileExists:
            executableName = neighbourBuildFile
            path = FLARE_PATH
        elif childBuildFileExists:
            executableName = LOCAL_NAME
            path = LOCAL_PATH
        else:
            raise FirmwareNotFound(f"No build files found for rocket named {rocket.rocket_name}")

        hw_sim = rocket.construct_hw_sim()

        if not hw_sim:
            raise Exception(f"No HW Sim defined for rocket named {rocket.rocket_name}")

        LOGGER.info(f"Using FW executable: {os.path.join(path, executableName)}")

        return SimConnection(
            path, executableName, hw_sim
        )


class FirmwareNotFound(Exception):
    pass
