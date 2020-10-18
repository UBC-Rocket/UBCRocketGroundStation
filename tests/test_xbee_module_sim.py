from threading import Lock
from time import sleep

from connections.sim.xbee_module_sim import XBeeModuleSim


class TestXBeeModuleSim:
    def setup_method(self):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        self.xbee = XBeeModuleSim()
        self.rkt_lock = Lock()
        self.gnd_lock = Lock()
        self.msgs_to_rocket = []
        self.msgs_to_ground = []

        def rocket_callback(data):
            with self.rkt_lock:
                self.msgs_to_rocket.append(data)

        def ground_callback(data):
            with self.gnd_lock:
                self.msgs_to_ground.append(data)

        self.xbee.rocket_callback = rocket_callback
        self.xbee.ground_callback = ground_callback

    def teardown_method(self):
        """ teardown any state that was previously setup with a setup_method
        call.
        """

    def test_rocket_rx(self):
        tx_example = bytearray(
            b"\x7E\x00\x16\x10\x01\x00\x7D\x33\xA2\x00\x40\x0A\x01\x27"
            b"\xFF\xFE\x00\x00\x54\x78\x44\x61\x74\x61\x30\x41\x7D\x33"
        )

        self.xbee.recieved_from_rocket(tx_example)
        sleep(0.1)

        assert self.msgs_to_ground == [b"TxData0A"]

    def test_ground_rx(self):
        self.xbee.send_to_rocket(b"HelloRocket")  # 11 bytes
        sleep(0.1)

        assert len(self.msgs_to_rocket[0]) == 27
        assert self.msgs_to_rocket[0][15:-1] == b"HelloRocket"

    def test_rocket_rx_pieces(self):
        tx_1 = bytearray(b"\x7E\x00\x16\x10\x01\x00\x7D\x33\xA2\x00\x40\x0A")
        tx_2 = bytearray(
            b"\x01\x27\xFF\xFE\x00\x00\x54\x78\x44\x61\x74\x61\x30\x41\x7D\x33"
        )

        self.xbee.recieved_from_rocket(tx_1)
        self.xbee.recieved_from_rocket(tx_2)
        sleep(0.1)

        assert self.msgs_to_ground == [b"TxData0A"]
