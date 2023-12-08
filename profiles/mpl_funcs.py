"""Receive and plot data"""

from textwrap import wrap
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from main_window.competition.comp_app import MAP_MARKER
from main_window.mplwidget import MplWidget
from profiles.label import Label


def receive_map(self) -> None:
    """
    Updates the UI when a new map is available for display
    """
    children = self.plot_widget.canvas.ax.get_children()
    for c in children:
        if isinstance(c, AnnotationBbox):
            c.remove()

    zoom, radius, map_image, mark = self.map_data.get_map_value()

    # plotMap UI modification
    self.plot_widget.canvas.ax.set_axis_off()
    self.plot_widget.canvas.ax.set_ylim(map_image.shape[0], 0)
    self.plot_widget.canvas.ax.set_xlim(0, map_image.shape[1])

    # Removes pesky white boarder
    self.plot_widget.canvas.fig.subplots_adjust(
        left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    if self.im:
        # Required because plotting images over old ones creates memory leak
        # NOTE: im.set_data() can also be used
        self.im.remove()

    self.im = self.plot_widget.canvas.ax.imshow(map_image)

    # updateMark UI modification
    for i, m in enumerate(mark):
        annotation_box = AnnotationBbox(OffsetImage(MAP_MARKER), m, frameon=False)
        self.plot_widget.canvas.ax.add_artist(annotation_box)

    self.plot_widget.canvas.draw()


def receive_time_series(self, plot_widget: MplWidget, label: Label) -> None:
    """
        Setup for plotting time series
        Clear previous plot, change subplot settings
    """
    children = plot_widget.canvas.ax.get_children()

    # clear children if still exist from last plot
    for c in children:
        if isinstance(c, AnnotationBbox):
            c.remove()

    plot_widget.canvas.fig.subplots_adjust(
        left=0.2, bottom=0.1, right=0.95, top=0.9, wspace=0, hspace=0)

    if self.im:
        # Required because plotting images over old ones creates memory leak
        # NOTE: im.set_data() can also be used
        self.im.remove()

    self.im = None

    is_acceleration = "Acceleration" in label.name
    if is_acceleration and not plot_widget.showing_checkboxes:
        plot_widget.show_checkboxes()

    # Plot data on graph
    plot_widget.canvas.ax.set_axis_on()
    plot_widget.canvas.ax.set_aspect('auto')

    plot_widget.canvas.ax.cla()
    data_entry_id = self.rocket_profile.label_to_data_id[label.name]

    if is_acceleration:
        labels = ["X", "Y", "Z"]
        colors = ["Red", "Blue", "Green"]
        plot_data = False

        for i, checkbox in enumerate(plot_widget.accel_checkboxes):
            if checkbox.isChecked():
                plot_data = True  # there is data to plot
                t, y = self.rocket_data.time_series_by_device(label.device, data_entry_id[i])
                plot_widget.canvas.ax.plot(t, y, color=colors[i], label=labels[i])

        if plot_data:
            plot_widget.canvas.ax.legend(loc="upper right")

    elif data_entry_id and self.rocket_data.time_series_by_device(label.device, data_entry_id):

        t, y = self.rocket_data.time_series_by_device(label.device, data_entry_id)

        if y is None:
            pass  # possible TODO: log if no data found

        elif data_entry_id == data_entry_id.STATE:
            # Figure width in pixels
            fig_width = plot_widget.canvas.fig.get_size_inches()[0] * plot_widget.canvas.fig.dpi
            # Trim state name (STATE_LANDED -> LANDED)
            plot_widget.canvas.ax.plot(t, ['\n'.join(wrap(e.name[6:], int(fig_width * 0.015))) for e in y])

            plot_widget.canvas.ax.tick_params(axis='y', labelsize=6)

        else:
            plot_widget.canvas.ax.plot(t, y)
            plot_widget.canvas.ax.grid()

    plot_widget.canvas.ax.set_xlabel("Time (ms)")
    plot_widget.canvas.ax.set_ylabel(f"{label.name} ({self.rocket_profile.label_unit[label.name]})")

    plot_widget.canvas.ax.set_title(f"{label.device.name} {label.name}", fontsize=10, pad=10, wrap=True)
    plot_widget.canvas.draw()
