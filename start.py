import main

window = None


def start(*args, **kwargs):  # TODO: does this need its own file??
    global window

    window = main.MainApp(*args, **kwargs)
    window.show()
