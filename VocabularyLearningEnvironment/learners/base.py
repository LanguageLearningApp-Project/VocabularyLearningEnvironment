from abc import ABC, abstractmethod
from teacher.items import TeachingItem
from copy import deepcopy


class BaseLearner(ABC):
    @abstractmethod
    def reply(self, question, *args, **kwargs):
        pass
    
    @abstractmethod
    def learn(self, item: TeachingItem, *args, **kwargs):
        pass
    
    def deepcopy(self):
        return deepcopy(self)