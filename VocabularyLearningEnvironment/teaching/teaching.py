from abc import ABC, abstractmethod
from typing import List
from .items import TeachingItem
import random

class BaseLearner(ABC):
    @abstractmethod
    def reply(self, question):
        pass


class BaseTeacher(ABC):
    
    def __init__(self, material: List[TeachingItem]):
        is_list = isinstance(material, list)
        contains_teaching_items = all(isinstance(item, TeachingItem) for item in material)
        print(is_list, contains_teaching_items)
        if not is_list or not(material) or not contains_teaching_items:
            raise TypeError("material must be a non-empty list of TeachingItem instances")
        self.material = material
    
    @abstractmethod
    def choose_item(self):
        pass
    
    @abstractmethod
    def gets_answer(self, queried_item: TeachingItem, answer):
        pass
    
    

class RandomTeacher(BaseTeacher):
    def choose_item(self):
        return random.choice(self.material)
    
    def gets_answer(self, queried_item, answer):
        pass