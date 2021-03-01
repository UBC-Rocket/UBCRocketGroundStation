import struct
from enum import Enum

from main_window.data_entry_id import DataEntryIds
from main_window.packet_parser import SubpacketIds
from main_window.competition.comp_packet_parser import SubpacketIds as SubpacketIds_Comp


def bulk_sensor(time: int, barometer_altitude: float, acceleration_x: float, acceleration_y: float,
                acceleration_z: float, orientation_1: float, orientation_2: float, orientation_3: float,
                latitude: float, longitude: float, state: int) -> bytearray:
    """

    :return:
    :rtype: bytearray
    """
    bulk_sensor_arr: bytearray = bytearray()
    bulk_sensor_arr.append(SubpacketIds_Comp.BULK_SENSOR.value)  # id
    bulk_sensor_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    bulk_sensor_arr.extend(struct.pack(">f", barometer_altitude))  # barometer altitude
    bulk_sensor_arr.extend(struct.pack(">f", acceleration_x))  # Acceleration X
    bulk_sensor_arr.extend(struct.pack(">f", acceleration_y))  # Acceleration Y
    bulk_sensor_arr.extend(struct.pack(">f", acceleration_z))  # Acceleration Z
    bulk_sensor_arr.extend(struct.pack(">f", orientation_1))  # Orientation
    bulk_sensor_arr.extend(struct.pack(">f", orientation_2))  # Orientation
    bulk_sensor_arr.extend(struct.pack(">f", orientation_3))  # Orientation
    bulk_sensor_arr.extend(struct.pack(">f", latitude))  # Latitude
    bulk_sensor_arr.extend(struct.pack(">f", longitude))  # Longitude
    bulk_sensor_arr.extend(state.to_bytes(length=2, byteorder='big'))  # State
    return bulk_sensor_arr

def single_sensor(time: int, sensor_id: SubpacketIds, value: float) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(sensor_id.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend(struct.pack(">f", value))  # barometer altitude
    return data_arr


class StatusType(Enum):
    NOMINAL = 0b00
    NON_CRITICAL_FAILURE = 0b01
    CRITICAL_FAILURE = 0b11


# TODO: Abstract sensor & other status away from bitfield values for the parameters
def status_ping(time: int, status: StatusType, sensor_status_msb: int, sensor_status_lsb: int, other_status_msb: int,
                other_status_lsb: int) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds_Comp.STATUS_PING.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # use current integer time

    data_arr.extend((int(status.value)).to_bytes(length=1, byteorder='big'))  # status

    # BAROMETER, GPS, ACCELEROMETER, IMU, TEMPERATURE
    data_arr.extend((int(sensor_status_msb)).to_bytes(length=1, byteorder='big'))
    data_arr.extend((int(sensor_status_lsb)).to_bytes(length=1, byteorder='big'))

    # DROGUE_IGNITER_CONTINUITY, MAIN_IGNITER_CONTINUITY, FILE_OPEN_SUCCESS
    data_arr.extend((int(other_status_msb)).to_bytes(length=1, byteorder='big'))
    data_arr.extend((int(other_status_lsb)).to_bytes(length=1, byteorder='big'))
    return data_arr


def message(time: int, message: str) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """

    if len(message) > 250:
        raise ValueError("Message too long for packet")

    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds.MESSAGE.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend((len(message)).to_bytes(length=1, byteorder='big'))  # length of the message data
    data_arr.extend([ord(ch) for ch in message])  # message
    return data_arr


def config(time: int, is_sim: bool, rocket_type: int, version_id: str) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds.CONFIG.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend((int(1 if is_sim else 0)).to_bytes(length=1, byteorder='big'))  # is sim
    data_arr.extend((int(rocket_type)).to_bytes(length=1, byteorder='big'))  # rocket type
    data_arr.extend([ord(ch) for ch in version_id])  # version id
    return data_arr


def event(time: int, event: int) -> bytearray:
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds.EVENT.value)
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))
    data_arr.extend((int(event)).to_bytes(length=2, byteorder='big'))
    return data_arr


def state(time: int, state: int) -> bytearray:
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds.STATE.value)
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))
    data_arr.extend((int(state)).to_bytes(length=2, byteorder='big'))
    return data_arr

def gps(time: int, latitude: float, longitude: float, gps_altitude: float) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds_Comp.GPS.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend(struct.pack(">f", latitude))  # Latitude
    data_arr.extend(struct.pack(">f", longitude))  # Longitude
    data_arr.extend(struct.pack(">f", gps_altitude))  # barometer altitude
    return data_arr


def orientation(time: int,  orientation_1: float, orientation_2: float,
                orientation_3: float, orientation_4: float) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketIds_Comp .ORIENTATION.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend(struct.pack(">f", orientation_1))  # Orientation
    data_arr.extend(struct.pack(">f", orientation_2))  # Orientation
    data_arr.extend(struct.pack(">f", orientation_3))  # Orientation
    data_arr.extend(struct.pack(">f", orientation_4))  # Orientation
    return data_arr
