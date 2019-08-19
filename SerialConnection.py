from IConnection import IConnection
from digi.xbee.devices import XBeeDevice


class SerialConnection(IConnection):

    def __init__(self, comPort, baudRate):
        self.device = XBeeDevice(comPort, baudRate)
        self.device.set_sync_ops_timeout(5) #5 seconds
        self.device.open()

    def get(self):
        message = self.device.read_data()
        if message:
            return message.data

    def send(self, data):
        # remote_device = RemoteXBeeDevice(self.device, XBee64BitAddress.from_hex_string("0013A20041678fb9"))
        # self.device.send_data(remote_device, bytes)
        self.device.send_data_broadcast(bytes)