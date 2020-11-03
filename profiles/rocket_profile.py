from abc import ABC, abstractmethod


class RocketProfile(ABC):
    @property
    @abstractmethod
    def rocket_name(self):
        pass

    @property
    @abstractmethod
    def buttons(self):
        pass

    @property
    @abstractmethod
    def labels(self):
        pass

    '''
    Factory pattern for objects that should only be constructed if needed
    '''
    @abstractmethod
    def construct_hw_sim(self):
        pass
