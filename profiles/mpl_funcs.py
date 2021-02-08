from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from main_window.competition.comp_app import MAP_MARKER
from main_window.main_app import MainApp


def receive_map(self: MainApp) -> None:
    """
    Updates the UI when a new map is available for display
    """
    children = self.plotWidget.canvas.ax.get_children()
    for c in children:
        if isinstance(c, AnnotationBbox):
            c.remove()

    zoom, radius, map_image, mark = self.map_data.get_map_value()

    # plotMap UI modification
    self.plotWidget.canvas.ax.set_axis_off()
    self.plotWidget.canvas.ax.set_ylim(map_image.shape[0], 0)
    self.plotWidget.canvas.ax.set_xlim(0, map_image.shape[1])

    # Removes pesky white boarder
    self.plotWidget.canvas.fig.subplots_adjust(
        left=0, bottom=0, right=1, top=1, wspace=0, hspace=0
    )

    if self.im:
        # Required because plotting images over old ones creates memory leak
        # NOTE: im.set_data() can also be used
        self.im.remove()

    self.im = self.plotWidget.canvas.ax.imshow(map_image)

    # updateMark UI modification
    annotation_box = AnnotationBbox(OffsetImage(MAP_MARKER), mark, frameon=False)
    self.plotWidget.canvas.ax.add_artist(annotation_box)

    # For debugging marker position
    # self.plotWidget.canvas.ax.plot(mark[0], mark[1], marker='o', markersize=3, color="red")

    self.plotWidget.canvas.draw()
