from typing import Dict


class RocketProfile:
    def __init__(self, buttons: Dict[str, str]):
        self.buttons = buttons


tantalus = RocketProfile({"Arm": "arm", "Status": "status"})
co_pilot = RocketProfile(
    {"Arm": "arm", "Halo": "halo", "Data": "data", "Status": "status"}
)
