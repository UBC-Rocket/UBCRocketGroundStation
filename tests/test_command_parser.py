import pytest

from main_window.command_parser import CommandParser, CommandType, CommandParsingError
from main_window.device_manager import DeviceManager, DeviceType, is_device_type_flare


@pytest.fixture(scope="function")
def full_device_manager():
    device_manager = DeviceManager(None, None)
    for device in DeviceType:
        device_manager.register_device(device, None, ('CONNECTION', device.name))
    return device_manager


def test_parse_self(full_device_manager):
    command_parser = CommandParser(full_device_manager)

    available_commands = command_parser.available_commands()
    assert len(available_commands) == len(DeviceType) * len(CommandType)

    for command in available_commands:
        assert command_parser.pase_command(command) is not None


def test_format(full_device_manager):
    command_parser = CommandParser(full_device_manager)

    for device in DeviceType:
        if is_device_type_flare(device):
            for command in CommandType:
                assert command_parser.pase_command(f"{device.name}.{command.name}") == \
                       (device, command, bytes([command.value]))


def test_broadcast_format(full_device_manager):
    command_parser = CommandParser(full_device_manager)

    for command in CommandType:
        assert command_parser.broadcast_data(command) == bytes([command.value])


def test_bad_commannds(full_device_manager):
    bad_commands = [
        "NOT.A.COMMAND",
        f"{DeviceType.BNB_STAGE_1_FLARE.name}.NOT_A_COMMAND",
        f"{DeviceType.BNB_STAGE_1_FLARE.name}",
        f"NOT_A_DEVICE.{CommandType.ARM.name}",
        CommandType.ARM.name,
    ]

    command_parser = CommandParser(full_device_manager)
    for command in bad_commands:
        with pytest.raises(CommandParsingError):
            command_parser.pase_command(command)


def test_unregistered_device(full_device_manager):
    full_command_parser = CommandParser(full_device_manager)
    all_commands = full_command_parser.available_commands()

    device_manager = DeviceManager(None, None)
    device_manager.register_device(DeviceType.BNB_STAGE_1_FLARE, None, ('CONNECTION', DeviceType.BNB_STAGE_1_FLARE.name))
    command_parser = CommandParser(device_manager)

    for command in all_commands:
        (device, _, _) = full_command_parser.pase_command(command)
        if device == DeviceType.BNB_STAGE_1_FLARE:
            assert command_parser.pase_command(command) is not None
        else:
            with pytest.raises(CommandParsingError):
                command_parser.pase_command(command)
