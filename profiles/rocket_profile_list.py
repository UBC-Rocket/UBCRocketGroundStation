from typing import List

from .rocket_profile import RocketProfile

from .rockets.silvertip import SilvertipProfile
from .rockets.bnb import BNBProfile
from .rockets.tantalus import TantalusProfile
from .rockets.co_pilot import CoPilotProfile
from .rockets.hollyburn import HollyburnProfile
from .rockets.whistler_blackcomb import WbProfile
from .rockets.sunburst import SunburstProfile

ROCKET_PROFILES: List[RocketProfile] = [
    BNBProfile(),
    SilvertipProfile(),
    TantalusProfile(),
    CoPilotProfile(),
    HollyburnProfile(),
    WbProfile(),
    SunburstProfile(),
]