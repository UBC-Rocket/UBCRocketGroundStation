from typing import Dict, List

from .label import TYPE_CHECKING, Label
from connections.sim.hw_sim import HWSim

if TYPE_CHECKING:
    from main_window.main import MainApp


class RocketProfile:
    def __init__(
            self, rocket_name:str, buttons: Dict[str, str], labels: List[Label], hw_sim: HWSim = None
    ):
        self.rocket_name = rocket_name
        self.buttons = buttons
        self.labels = labels
        self.hw_sim = hw_sim