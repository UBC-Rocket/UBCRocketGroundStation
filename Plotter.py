import numpy as np
import matplotlib
from matplotlib import pyplot as plt

x = []
y = []

plt.ion()
plt.show()


def pause(interval):
    backend = plt.rcParams['backend']
    if backend in matplotlib.rcsetup.interactive_bk:
        figManager = matplotlib._pylab_helpers.Gcf.get_active()
        if figManager is not None:
            canvas = figManager.canvas
            if canvas.figure.stale:
                canvas.draw()
            canvas.start_event_loop(interval)
            return


def plot(newx, newy):
    global x
    global y
    x.append(newx)
    y.append(newy)
    plt.clf()
    plt.plot(x, y, marker="o")
    plt.draw()
    #pause(0.01)

def close():
    plt.close()
