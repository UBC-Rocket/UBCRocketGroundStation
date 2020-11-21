from io import BytesIO

from main_window.subpacket_ids import SubpacketEnum
from main_window.packet_parser import PacketParser, Header


class WbPacketParser(PacketParser):

    def __init__(self, bigEndianInts, bigEndianFloats):
        super().__init__(bigEndianInts, bigEndianFloats)

