from typing import Dict, List

from .label import TYPE_CHECKING, Label

if TYPE_CHECKING:
    from main import MainApp


class RocketProfile:
    def __init__(self, buttons: Dict[str, str], labels: List[Label]):
        self.buttons = buttons
        self.labels = labels

    def update_labels(self, main_window: "MainApp") -> None:
        for label in self.labels:
            getattr(main_window, label.name + "Label").setText(
                label.update(main_window)
            )
