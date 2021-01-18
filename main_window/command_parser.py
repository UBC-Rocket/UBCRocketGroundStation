from enum import Enum
from collections import namedtuple
from typing import List

from .device_manager import DeviceManager, DeviceType, is_device_type_flare
from .packet_parser import SubpacketIds

ParsedCommand = namedtuple('ParsedCommand', ('device_type', 'command_type', 'command_data'))


class CommandType(Enum):
    ARM = 0x41
    CONFIG = 0x43
    DISARM = 0x44
    PING = 0x50
    BULK = 0x30
    GPS = 0x04
    ORIENT = 0x06

    # "Single sensor values" 0x10~0x2F
    ACCELX = SubpacketIds.ACCELERATION_X.value
    ACCELY = SubpacketIds.ACCELERATION_Y.value
    ACCELZ = SubpacketIds.ACCELERATION_Z.value
    BAROPRES = SubpacketIds.PRESSURE.value
    BAROTEMP = SubpacketIds.BAROMETER_TEMPERATURE.value
    TEMP = SubpacketIds.TEMPERATURE.value
    LAT = SubpacketIds.LATITUDE.value
    LON = SubpacketIds.LONGITUDE.value
    GPSALT = SubpacketIds.GPS_ALTITUDE.value
    ALT = SubpacketIds.CALCULATED_ALTITUDE.value
    STATE = SubpacketIds.STATE.value
    VOLT = SubpacketIds.VOLTAGE.value
    GROUND = SubpacketIds.GROUND_ALTITUDE.value


class CommandParser:

    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager

    def pase_command(self, command_str: str) -> ParsedCommand:
        message_parts = command_str.split('.')

        if len(message_parts) != 2:
            raise CommandParsingError("Bad command format")

        (device_str, command_str) = message_parts

        try:
            device = DeviceType[device_str.upper()]
        except KeyError:
            raise CommandParsingError(f"Unknown device type: {device_str}")

        if self.device_manager.get_full_address(device) is None:
            raise CommandParsingError(f"Device not yet registered: {device.name}")

        try:
            command = CommandType[command_str.upper()]
        except KeyError:
            raise CommandParsingError(f"Unknown command: {command_str}")

        data = bytes([command.value])

        return ParsedCommand(device_type=device, command_type=command, command_data=data)

    def broadcast_data(self, command_type: CommandType):
        return bytes([command_type.value])

    def available_commands(self) -> List[str]:
        available_commands = []
        for device in DeviceType:
            if is_device_type_flare(device) and self.device_manager.get_full_address(device) is not None:
                for command in CommandType:
                    available_commands.append(f"{device.name}.{command.name}")
        return available_commands


class CommandParsingError(Exception):
    pass
