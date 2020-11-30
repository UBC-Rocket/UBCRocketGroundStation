import math
from io import BytesIO
from typing import Any, Dict, List

from util.detail import LOGGER
from util.event_stats import Event
from main_window.subpacket_ids import SubpacketEnum
from main_window.packet_parser import PacketParser, Header

BULK_SENSOR_EVENT = Event('bulk_sensor')

# TODO extract and cleanup https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
NOMINAL = 'NOMINAL'
NONCRITICAL_FAILURE = 'NONCRITICAL_FAILURE'
CRITICAL_FAILURE = 'CRITICAL_FAILURE'
OVERALL_STATUS = 'OVERALL_STATUS'
BAROMETER = 'BAROMETER'
GPS = 'GPS'
ACCELEROMETER = 'ACCELEROMETER'
TEMPERATURE = 'TEMPERATURE'
IMU = 'IMU'
SENSOR_TYPES = [BAROMETER, GPS, ACCELEROMETER, IMU, TEMPERATURE]
DROGUE_IGNITER_CONTINUITY = 'DROGUE_IGNITER_CONTINUITY'
MAIN_IGNITER_CONTINUITY = 'MAIN_IGNITER_CONTINUITY'
FILE_OPEN_SUCCESS = 'FILE_OPEN_SUCCESS'
OTHER_STATUS_TYPES = [DROGUE_IGNITER_CONTINUITY, MAIN_IGNITER_CONTINUITY, FILE_OPEN_SUCCESS]


class CompPacketParser(PacketParser):

    def __init__(self):
        super().__init__()

        self.register_packet(SubpacketEnum.GPS.value, self.gps)
        self.register_packet(SubpacketEnum.ORIENTATION.value, self.orientation)
        self.register_packet(SubpacketEnum.BULK_SENSOR.value, self.bulk_sensor)
        self.register_packet(SubpacketEnum.STATUS_PING.value, self.status_ping)

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
        if overall_status == 0b00000000:
            data[SubpacketEnum.STATUS_PING.value] = NOMINAL
        elif overall_status == 0b00000001:
            data[SubpacketEnum.STATUS_PING.value] = NONCRITICAL_FAILURE
        elif overall_status == 0b00000011:
            data[SubpacketEnum.STATUS_PING.value] = CRITICAL_FAILURE
        data[OVERALL_STATUS] = curr_byte  # TODO Review if safer this way
        LOGGER.info("Overall rocket status: %s", str(data[SubpacketEnum.STATUS_PING.value]))

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

        LOGGER.info(" - status of sensors" + ", %s" * len(SENSOR_TYPES),
                    *[sensor + ": " + str(data[sensor]) for sensor in SENSOR_TYPES])
        LOGGER.info(" - status of others" + ", %s" * len(OTHER_STATUS_TYPES),
                    *[other + ": " + str(data[other]) for other in OTHER_STATUS_TYPES])
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
        data: Dict[int, Any] = {}

        data[SubpacketEnum.CALCULATED_ALTITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ACCELERATION_X.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ACCELERATION_Y.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ACCELERATION_Z.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(byte_stream.read(4))  # TODO Remove soon?
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(byte_stream.read(4))  # TODO Remove soon?
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(byte_stream.read(4))  # TODO Remove soon?
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.STATE.value] = int.from_bytes(byte_stream.read(1), "big")

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
        data[SubpacketEnum.LATITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.LONGITUDE.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.GPS_ALTITUDE.value] = self.fourtofloat(byte_stream.read(4))
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

        # TODO Temporary dependency on subpacket enum, til we figure out https://trello.com/c/uFHtaN51/ https://trello.com/c/bA3RuHUC
        data[SubpacketEnum.ORIENTATION_1.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_2.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_3.value] = self.fourtofloat(byte_stream.read(4))
        data[SubpacketEnum.ORIENTATION_4.value] = self.fourtofloat(byte_stream.read(4))
        return data
