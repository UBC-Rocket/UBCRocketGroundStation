import GroundProcessing
import GroundSerial

GroundProcessing.initialize()

ids_set = set(map(lambda x: x[0][0].encode('ascii'), GroundProcessing.RADIOSET))

GroundSerial.init(GroundProcessing.addData, ids_set)
