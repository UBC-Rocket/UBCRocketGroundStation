from typing import Dict, List

from label import TYPE_CHECKING, Label, default_labels

if TYPE_CHECKING:
    from main import MainApp


class RocketProfile:
    def __init__(self, buttons: Dict[str, str], labels: List[Label]):
        self.buttons = buttons
        self.labels = labels

    def update_labels(self, main_window: "MainApp") -> None:
        for label in self.labels:
            getattr(main_window, label.name + "Label").setText(label.update(main_window))


tantalus = RocketProfile({"Arm": "arm", "Status": "status"}, default_labels)
co_pilot = RocketProfile(
    {"Arm": "arm", "Halo": "halo", "Data": "data", "Status": "status"},
    default_labels + [Label("Test", lambda main_window: "Hey")],
)
