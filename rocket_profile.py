import math
from typing import Dict


class RocketProfile:
    def __init__(self, buttons: Dict[str, str], labels: Dict[str, str]):
        self.buttons = buttons
        self.labels = labels

    def update_labels(self, main_window) -> None:
        for label in self.labels.items():
            exec(
                f"main_window.{label[0]}Label.setText(self.update_{label[1]}(main_window))"
            )


default_labels = {
    "Altitude": "altitude",
    "MaxAltitude": "max_altitude",
    "Gps": "gps",
    "State": "state",
    "Pressure": "pressure",
    "Acceleration": "acceleration",
}
