from typing import List

from .rocket_profile import RocketProfile

from .rockets.silvertip import SilvertipProfile
from .rockets.tantalus import BNBProfile
from .rockets.co_pilot import CoPilotProfile
from .rockets.hollyburn import HollyburnProfile
from .rockets.whistler_blackcomb import WbProfile

ROCKET_PROFILES: List[RocketProfile] = [
    SilvertipProfile(),
    BNBProfile(),
    CoPilotProfile(),
    HollyburnProfile(),
    WbProfile(),
]