from typing import Union

from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice
from digi.xbee.models.address import XBee64BitAddress

from ..connection import Connection, ConnectionMessage


class SerialConnection(Connection):

    def __init__(self, comPort: Union[int, str, None], baudRate: Union[int, None]):
        self.device = XBeeDevice(comPort, baudRate)
        self.device.set_sync_ops_timeout(5)  # 5 seconds
        self.device.open()
        self.device.add_data_received_callback(self._newData)

        self.callback = None

    def _newData(self, xbee_message):
        if self.callback:
            message = ConnectionMessage(
                hwid=str(xbee_message.remote_device.get_64bit_addr()),
                connection=self,
                data=xbee_message.data)

            self.callback(message)

    def registerCallback(self, fn):
        self.callback = fn

    def send(self, hwid, data):
        remote_device = RemoteXBeeDevice(self.device, XBee64BitAddress.from_hex_string(hwid))
        self.device.send_data(remote_device, bytes)

    def broadcast(self, data):
        self.device.send_data_broadcast(bytes)

    def shutdown(self):
        self.device.close()

    def isIntBigEndian(self):
        return True

    def isFloatBigEndian(self):
        return False
