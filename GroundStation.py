import GroundProcessing
import GroundSerial
import atexit

def exit_handler():
    print("Saving...")
    GroundProcessing.printToFile()
    print("Saved!")


atexit.register(exit_handler)

GroundProcessing.initialize()

ids_set = set(map(lambda x: x[0][0].encode('ascii'), GroundProcessing.RADIOSET))

GroundSerial.init(GroundProcessing.addData, ids_set)
