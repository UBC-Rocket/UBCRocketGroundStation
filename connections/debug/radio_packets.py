import struct
from main_window.subpacket_ids import SubpacketEnum
from enum import Enum


def bulk_sensor(time: int, barometer_altitude: float, acceleration_x: float, acceleration_y: float,
                acceleration_z: float, orientation_1: float, orientation_2: float, orientation_3: float,
                latitude: float, longitude: float, state: int) -> bytearray:
    """

    :return:
    :rtype: bytearray
    """
    bulk_sensor_arr: bytearray = bytearray()
    bulk_sensor_arr.append(SubpacketEnum.BULK_SENSOR.value)  # id
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
    bulk_sensor_arr.extend(state.to_bytes(length=1, byteorder='big'))  # State
    return bulk_sensor_arr

def single_sensor(time: int, sensor_id: int, value: float) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(sensor_id)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend(struct.pack(">f", value))  # barometer altitude
    return data_arr

class StatusType(Enum):
    NOMINAL = 0b00
    NON_CRITICAL_FAILURE = 0b01
    CRITICAL_FAILURE = 0b10


# TODO: Abstract sensor & other status away from bitfield values for the parameters
def status_ping(time: int, status: StatusType, sensor_status_msb: int, sensor_status_lsb: int, other_status_msb: int,
                other_status_lsb: int) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketEnum.STATUS_PING.value)  # id
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
    data_arr.append(SubpacketEnum.MESSAGE.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend((len(message)).to_bytes(length=1, byteorder='big'))  # length of the message data
    data_arr.extend([ord(ch) for ch in message])  # message
    return data_arr


def config(time: int, is_sim: bool, rocket_type: int) -> bytearray:
    """

    :return: data_arr
    :rtype: bytearray
    """
    data_arr: bytearray = bytearray()
    data_arr.append(SubpacketEnum.CONFIG.value)  # id
    data_arr.extend((int(time)).to_bytes(length=4, byteorder='big'))  # time
    data_arr.extend((int(2)).to_bytes(length=1, byteorder='big'))  # length of the config
    data_arr.extend((int(1 if is_sim else 0)).to_bytes(length=1, byteorder='big'))  # is sim
    data_arr.extend((int(rocket_type)).to_bytes(length=1, byteorder='big'))  # rocket type
    return data_arr
