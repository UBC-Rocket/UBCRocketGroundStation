from typing import List

from .rocket_profile import RocketProfile

from .rockets.tantalus import TantalusProfile
from .rockets.co_pilot import CoPilotProfile
from .rockets.whistler_blackcomb import WbProfile

ROCKET_PROFILES: List[RocketProfile] = [
    TantalusProfile(),
    CoPilotProfile(),
    WbProfile(),
]