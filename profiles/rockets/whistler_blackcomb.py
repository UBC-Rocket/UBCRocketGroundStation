from ..rocket_profile import RocketProfile
from main_window.whistler_blackcomb.wb_app import WbApp


class WbProfile(RocketProfile):

    @property
    def rocket_name(self):
        return "Whistler Blackcomb"

    @property
    def buttons(self):
        return None

    @property
    def labels(self):
        return None

    @property
    def sim_executable_name(self):
        return None

    def construct_hw_sim(self):
        # Assemble HW here
        return None

    def construct_app(self, connection):
        return WbApp(connection, self)
