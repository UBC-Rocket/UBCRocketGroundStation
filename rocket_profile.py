from typing import Dict, List

from label import Label, default_labels


class RocketProfile:
    def __init__(self, buttons: Dict[str, str], labels: List[Label]):
        self.buttons = buttons
        self.labels = labels

    def update_labels(self, main_window) -> None:
        for label in self.labels:
            exec(f"main_window.{label.name}Label.setText(label.update(main_window))")


tantalus = RocketProfile({"Arm": "arm", "Status": "status"}, default_labels)
co_pilot = RocketProfile(
    {"Arm": "arm", "Halo": "halo", "Data": "data", "Status": "status"},
    default_labels + [Label("Test", lambda main_window: "Hey")],
)
