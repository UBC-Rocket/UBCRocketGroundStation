import abc
from typing import Union


class ConnectionFactory(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def connection_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def requires_com_port(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def requires_baud_rate(self) -> bool:
        pass

    @abc.abstractmethod
    def construct(
        self,
        comPort: Union[int, str, None] = None,
        baudRate: Union[int, None] = None,
        rocket=None,
    ) -> None:
        pass
