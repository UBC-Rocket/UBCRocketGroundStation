from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.animation import FuncAnimation

from main_window.competition.comp_app import MAP_MARKER
from main_window.device_manager import DeviceType
from main_window.data_entry_id import DataEntryIds
from main_window.main_app import MainApp
from textwrap import wrap

from main_window.mplwidget import MplWidget

label_to_dataID = {"Altitude":DataEntryIds.CALCULATED_ALTITUDE,
                   "State":DataEntryIds.STATE,
                   "Stage2State":DataEntryIds.STATE,
                   "Pressure":DataEntryIds.PRESSURE,
                   "Acceleration": DataEntryIds.ACCELERATION_X,
                   }

def receive_map(self, plot_widget: MplWidget, device:DeviceType, label_name:str) -> None:
    """
    Updates the UI when a new map is available for display
    """
    children = plot_widget.canvas.ax.get_children()
    for c in children:
        if isinstance(c, AnnotationBbox):
            c.remove()

    zoom, radius, map_image, mark = self.map_data.get_map_value()

    # plotMap UI modification
    plot_widget.canvas.ax.set_axis_off()
    plot_widget.canvas.ax.set_ylim(map_image.shape[0], 0)
    plot_widget.canvas.ax.set_xlim(0, map_image.shape[1])

    # Removes pesky white boarder
    plot_widget.canvas.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

    if self.im:
        # Required because plotting images over old ones creates memory leak
        # NOTE: im.set_data() can also be used
        self.im.remove()

    self.im = plot_widget.canvas.ax.imshow(map_image)


    # updateMark UI modification
    for i in range(len(mark)):
        annotation_box = AnnotationBbox(OffsetImage(MAP_MARKER), mark[i], frameon=False)
        plot_widget.canvas.ax.add_artist(annotation_box)

    plot_widget.canvas.draw()



def receive_time_series(self, plot_widget: MplWidget, device:DeviceType, label_name:str) -> None:
    """
        Setup for plotting time series
        Clear previous plot, change subplot settings
    """
    children = plot_widget.canvas.ax.get_children()

    #clear children if still exist from last plot
    for c in children:
        if isinstance(c, AnnotationBbox):
            c.remove()

    plot_widget.canvas.fig.subplots_adjust(left=0.2, bottom=0.1, right=0.95, top=0.9, wspace=0, hspace=0)

    if self.im:
        # Required because plotting images over old ones creates memory leak
        # NOTE: im.set_data() can also be used
        self.im.remove()

    self.im = None

    plot_widget.canvas.ax.set_axis_on()
    plot_widget.canvas.ax.set_aspect('auto')

    plot_time_series(self, plot_widget, device, label_name)


def plot_time_series(self, plot_widget: MplWidget, device:DeviceType, label_name:str) -> None:
    """
            Updates the UI when time series data is available for display
    """
    data_entry_id = label_to_dataID[label_name]
    t, y = self.rocket_data.time_series_by_device(device, data_entry_id)

    plot_widget.canvas.ax.cla()

    if data_entry_id == data_entry_id.STATE:

        #Trim state name (STATE_LANDED -> LANDED), wrap state labels so they fit within the window
        fig_width = plot_widget.canvas.fig.get_size_inches()[0]*plot_widget.canvas.fig.dpi #figure width in pixels
        plot_widget.canvas.ax.plot(t, ['\n'.join(wrap(e.name[6:], int(fig_width*0.015))) for e in y])

        plot_widget.canvas.ax.tick_params(axis='y', labelsize=6)

    else:
        plot_widget.canvas.ax.scatter(t, y)

    plot_widget.canvas.ax.set_title(f"{device.name} {label_name}", fontsize=10, pad=10, wrap=True)
    plot_widget.canvas.draw()
