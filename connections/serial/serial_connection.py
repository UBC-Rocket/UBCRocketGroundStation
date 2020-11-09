from typing import Union

from digi.xbee.devices import XBeeDevice

from ..connection import Connection


class SerialConnection(Connection):

    def __init__(self, comPort: Union[int, str, None], baudRate: Union[int, None]):
        self.device = XBeeDevice(comPort, baudRate)
        self.device.set_sync_ops_timeout(5)  # 5 seconds
        self.device.open()
        self.device.add_data_received_callback(self._newData)

        self.callback = None

    def _newData(self, xbee_message):
        if self.callback:
            self.callback(xbee_message.data)

    def registerCallback(self, fn):
        self.callback = fn

    def send(self, data):
        # remote_device = RemoteXBeeDevice(self.device, XBee64BitAddress.from_hex_string("0013A20041678fb9"))
        # self.device.send_data(remote_device, bytes)
        self.device.send_data_broadcast(bytes)

    def shutdown(self):
        pass

    def isIntBigEndian(self):
        return True

    def isFloatBigEndian(self):
        return False
