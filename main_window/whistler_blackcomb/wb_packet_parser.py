from io import BytesIO

from main_window.data_entry_id import DataEntryIds
from main_window.packet_parser import PacketParser, Header


class WbPacketParser(PacketParser):

    def __init__(self, bigEndianInts, bigEndianFloats):
        super().__init__(bigEndianInts, bigEndianFloats)

