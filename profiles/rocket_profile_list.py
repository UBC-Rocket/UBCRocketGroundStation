from .rocket_profile import RocketProfile

from .rockets.silvertip import SilvertipProfile
from .rockets.tantalus import TantalusProfile
from .rockets.co_pilot import CoPilotProfile
from .rockets.hollyburn import HollyburnProfile
from .rockets.whistler_blackcomb import WbProfile

ROCKET_PROFILES: list[RocketProfile] = [
    SilvertipProfile(),
    TantalusProfile(),
    CoPilotProfile(),
    HollyburnProfile(),
    WbProfile(),
]
