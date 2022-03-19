import math
from enum import Enum
from io import BytesIO
from typing import Any, Dict, List

from util.detail import LOGGER
from util.event_stats import Event
from main_window.data_entry_id import DataEntryIds, DataEntryValues
from main_window.packet_parser import PacketParser, Header

BULK_SENSOR_EVENT = Event('bulk_sensor')

# Aggregated DataEntryIds for iteration. Outside function for access by tests
SENSOR_TYPES = [DataEntryIds.BAROMETER, DataEntryIds.GPS, DataEntryIds.ACCELEROMETER, DataEntryIds.IMU, DataEntryIds.TEMPERATURE, DataEntryIds.VOLTAGE]
OTHER_STATUS_TYPES = [DataEntryIds.DROGUE_IGNITER_CONTINUITY, DataEntryIds.MAIN_IGNITER_CONTINUITY, DataEntryIds.FILE_OPEN_SUCCESS]

# Converting bit array status to readable values
BITARRAY_TO_STATUS = {
    0b00000000: DataEntryValues.STATUS_NOMINAL,
    0b00000001: DataEntryValues.STATUS_NONCRITICAL_FAILURE,
    0b00000011: DataEntryValues.STATUS_CRITICAL_FAILURE,
}

# Parser's subpacket ids, according to spec. NOT DataIds
class SubpacketIds(Enum):
    STATUS_PING = 0x00
    GPS = 0x04
    ORIENTATION = 0x06
    BULK_SENSOR = 0x30

class CompPacketParser(PacketParser):

    def __init__(self):
        super().__init__()

        self.register_packet(SubpacketIds.GPS.value, self.gps)
        self.register_packet(SubpacketIds.ORIENTATION.value, self.orientation)
        self.register_packet(SubpacketIds.BULK_SENSOR.value, self.bulk_sensor)
        self.register_packet(SubpacketIds.STATUS_PING.value, self.status_ping)

    def status_ping(self, byte_stream: BytesIO, header: Header):
        """
        Convert bit field into a series of statuses

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        sensor_bit_field_length = 16
        other_bit_field_length = 16

        data: Dict = {}
        curr_byte: int = byte_stream.read(1)[0]

        # Overall status from 6th and 7th bits
        overall_status = curr_byte & 0b11
        data[DataEntryIds.OVERALL_STATUS] = BITARRAY_TO_STATUS[overall_status]

        # save since we do multiple passes over each byte
        byte_list: List[int] = [b for b in byte_stream.read(2)]
        # Sensor status
        num_assigned_bits = min(sensor_bit_field_length, len(SENSOR_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = math.floor(i / 8)  # 0 based index, of byte out of current group
            relative_bit_index = 7 - (i % 8)  # get the bits left to right
            data[SENSOR_TYPES[i]] = self.bitfrombyte(byte_list[byte_index], relative_bit_index)

        byte_list: List[int] = [b for b in byte_stream.read(2)]
        # Other misc statuses
        num_assigned_bits = min(other_bit_field_length, len(OTHER_STATUS_TYPES))  # only go as far as is assigned
        for i in range(0, num_assigned_bits):
            byte_index = math.floor(i / 8)
            relative_bit_index = 7 - (i % 8)
            data[OTHER_STATUS_TYPES[i]] = self.bitfrombyte(byte_list[byte_index], relative_bit_index)

        LOGGER.info("Overall rocket status: %s", str(data[DataEntryIds.OVERALL_STATUS]))
        LOGGER.info(" - status of sensors" + ", %s" * len(SENSOR_TYPES),
                    *[sensor.name + ": " + str(data[sensor]) for sensor in SENSOR_TYPES])
        LOGGER.info(" - status of others" + ", %s" * len(OTHER_STATUS_TYPES),
                    *[other.name + ": " + str(data[other]) for other in OTHER_STATUS_TYPES])
        return data

    def bulk_sensor(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        data: Dict[DataEntryIds, Any] = {}

        data[DataEntryIds.CALCULATED_ALTITUDE] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ACCELERATION_X] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ACCELERATION_Y] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ACCELERATION_Z] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ORIENTATION_1] = self.fourtofloat(byte_stream.read(4))  # TODO Remove soon?
        data[DataEntryIds.ORIENTATION_2] = self.fourtofloat(byte_stream.read(4))  # TODO Remove soon?
        data[DataEntryIds.ORIENTATION_3] = self.fourtofloat(byte_stream.read(4))  # TODO Remove soon?
        data[DataEntryIds.LATITUDE] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.LONGITUDE] = self.fourtofloat(byte_stream.read(4))
        state_data = super().state(byte_stream, header, print_state=False)
        data[DataEntryIds.STATE] = state_data[DataEntryIds.STATE]

        BULK_SENSOR_EVENT.increment()
        return data

    def gps(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        data = {}

        data[DataEntryIds.LATITUDE] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.LONGITUDE] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.GPS_ALTITUDE] = self.fourtofloat(byte_stream.read(4))
        return data

    def orientation(self, byte_stream: BytesIO, header: Header):
        """

        :param byte_stream:
        :type byte_stream:
        :param header:
        :type header:
        :return:
        :rtype:
        """
        data = {}

        data[DataEntryIds.ORIENTATION_1] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ORIENTATION_2] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ORIENTATION_3] = self.fourtofloat(byte_stream.read(4))
        data[DataEntryIds.ORIENTATION_4] = self.fourtofloat(byte_stream.read(4))
        return data
