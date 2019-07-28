import main

window = None




def start(com, baud):
    global window

    window = main.MainApp(com, baud)
    window.show()
