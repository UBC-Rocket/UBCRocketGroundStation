from abc import ABC, abstractmethod
from connections.connection import Connection


class RocketProfile(ABC):
    @property
    @abstractmethod
    def rocket_name(self) -> str:
        pass

    @property
    @abstractmethod
    def buttons(self):
        pass

    @property
    @abstractmethod
    def labels(self):
        pass

    @property
    @abstractmethod
    def sim_executable_name(self):
        pass

    '''
    Factory pattern for objects that should only be constructed if needed
    '''
    @abstractmethod
    def construct_hw_sim(self):
        # Here we can define HW Sim and all its sensors etc. without them being constructed if we aren't running SIM.
        # This is useful as HW Sim may be multi-threaded or do something upon construction that we dont want to
        # happen during regular flight.
        pass

    @abstractmethod
    def construct_app(self, connection: Connection):
        pass
