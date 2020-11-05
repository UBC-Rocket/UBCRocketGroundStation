import os
import sys
from typing import Union

from util.detail import LOCAL

from ..connection_factory import ConnectionFactory
from .sim_connection import SimConnection
from pathlib import Path


FLARE_PATH = os.path.join(Path(LOCAL).parent, 'FLARE', 'avionics', 'build')

LOCAL_PATH = os.path.join(LOCAL, 'FW')

LOCAL_NAME = 'program' + '.exe' if sys.platform == 'win32' else ''


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

        # Check FW (child) dir and FLARE (neighbour) dir for rocket build files
        # If multiple build files found throw exception
        if os.path.exists(FLARE_PATH):
            neighbourBuildFiles = [s for s in os.listdir(FLARE_PATH) if rocket.rocket_name.lower() in s.lower()]
            neighbourBuildFileExists = bool(neighbourBuildFiles)
        else:
            neighbourBuildFileExists = False

        childBuildFileExists = LOCAL_NAME in os.listdir(LOCAL_PATH)

        if childBuildFileExists and neighbourBuildFileExists:
            raise Exception(
                f"Multiple build files found: {neighbourBuildFiles[0]} and {LOCAL_NAME}")
        elif neighbourBuildFileExists:
            executableName = neighbourBuildFiles[0]
            path = FLARE_PATH
        elif childBuildFileExists:
            executableName = LOCAL_NAME
            path = LOCAL_PATH
        else:
            raise Exception(f"No build files found for rocket named {rocket.rocket_name}")

        hw_sim = rocket.construct_hw_sim()

        if not hw_sim:
            raise Exception(f"No HW Sim defined for rocket named {rocket.rocket_name}")

        return SimConnection(
            path, executableName, hw_sim
        )
