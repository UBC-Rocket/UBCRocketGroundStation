import pytest
from unittest.mock import MagicMock

from connections.sim.hw.xbee_module_sim import XBeeModuleSim, FRAME_PARSED_EVENT, SENT_TO_ROCKET_EVENT
from util.event_stats import get_event_stats_snapshot

TEST_GS_ADDR = bytes.fromhex('0013A200400A0127')
TEST_GS_ADDR_ESCAPED = bytes.fromhex('007D33A200400A0127')


@pytest.fixture()
def xbee():
    xbee = XBeeModuleSim(TEST_GS_ADDR)
    xbee.rocket_callback = MagicMock()
    xbee.ground_callback = MagicMock()
    yield xbee
    xbee.shutdown()


def test_rocket_rx(xbee):
    test_data = b"TxData0A"
    tx_example = bytearray(
        b"\x7E\x00\x16\x10\x01" + TEST_GS_ADDR_ESCAPED +
        b"\xFF\xFE\x00\x00" + test_data + b"\x7D\x33"
    )

    snapshot = get_event_stats_snapshot()
    xbee.recieved_from_rocket(tx_example)

    assert FRAME_PARSED_EVENT.wait(snapshot) == 1
    xbee.ground_callback.assert_called_with(test_data)


def test_ground_rx(xbee):
    snapshot = get_event_stats_snapshot()
    xbee.send_to_rocket(b"HelloRocket")  # 11 bytes

    assert SENT_TO_ROCKET_EVENT.wait(snapshot) == 1

    msg = xbee.rocket_callback.call_args[0][0]

    # Skip any escape characters
    assert len(msg) - msg.count(b'\x7D') == 27

    assert msg[-12:-1] == b"HelloRocket"


def test_rocket_rx_pieces(xbee):
    test_data = b"TxData0A"
    tx_1 = bytearray(b"\x7E\x00\x16\x10\x01") + TEST_GS_ADDR_ESCAPED[:7]
    tx_2 = bytearray(TEST_GS_ADDR_ESCAPED[7:] + b"\xFF\xFE\x00\x00" + test_data + b"\x7D\x33")

    snapshot = get_event_stats_snapshot()
    xbee.recieved_from_rocket(tx_1)
    xbee.recieved_from_rocket(tx_2)

    assert FRAME_PARSED_EVENT.wait(snapshot) == 1
    xbee.ground_callback.assert_called_with(test_data)

def test_rocket_rx_bad_addr(xbee):
    test_data = b"TxData0A"
    tx_example = bytearray(
        b"\x7E\x00\x16\x10\x01" + bytes(8) +
        b"\xFF\xFE\x00\x00" + test_data + b"\x3A"
    )

    snapshot = get_event_stats_snapshot()
    xbee.recieved_from_rocket(tx_example)

    assert FRAME_PARSED_EVENT.wait(snapshot) == 1
    assert xbee.ground_callback.call_count == 0
