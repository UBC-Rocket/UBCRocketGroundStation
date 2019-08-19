import main

window = None




def start(connection): #TODO: does this need its own file??
    global window

    window = main.MainApp(connection)
    window.show()
