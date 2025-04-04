from dataclasses import dataclass
from abc import ABC, abstractmethod

class TeachingItem(ABC):
    @abstractmethod
    def is_answer_correct(self, answer) -> bool:
        pass


@dataclass
class WordItem:
    source: str
    target: str
    
    def is_answer_correct(self, answer: str) -> bool:
        return self.target == answer