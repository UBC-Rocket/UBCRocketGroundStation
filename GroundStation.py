import GroundSerial

window = None




def start(com, baud):
    global window

    window = GroundSerial.MainApp(com, baud)
    window.show()
