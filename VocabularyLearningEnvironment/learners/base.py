from abc import ABC, abstractmethod
from teaching.items import TeachingItem


class BaseLearner(ABC):
    @abstractmethod
    def reply(self, question, *args, **kwargs):
        pass
    
    @abstractmethod
    def learn(self, item: TeachingItem, *args, **kwargs):
        pass
