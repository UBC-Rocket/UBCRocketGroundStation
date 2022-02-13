from abc import ABC, abstractmethod
from enum import Enum, auto


class SensorType(Enum):
    GPS = auto()
    IMU = auto()
    ACCELEROMETER = auto()
    BAROMETER = auto()
    TEMPERATURE = auto()
    THERMOCOUPLE = auto()
    VOLTAGE = auto()


REQUIRED_SENSOR_FLOATS = {
    SensorType.GPS: 3,
    SensorType.IMU: 4,
    SensorType.ACCELEROMETER: 3,
    SensorType.BAROMETER: 2,
    SensorType.TEMPERATURE: 1,
    SensorType.THERMOCOUPLE: 1,
    SensorType.VOLTAGE: 1
}


class Sensor(ABC):

    @abstractmethod
    def read(self) -> tuple:
        # TODO: Ideally we should try to further decouple HW sim from the SIM protocol by finding a way to make the
        #  return values order invariant.
        pass

    @abstractmethod
    def get_type(self) -> SensorType:
        pass
