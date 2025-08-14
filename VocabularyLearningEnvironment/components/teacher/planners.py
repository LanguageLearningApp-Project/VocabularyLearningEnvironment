from .base import Planner
from .planning_contexts import PlanningContext
from typing import List
from .items import TeachingItem
from wordfreq import top_n_list
import random


class RandomPlanner(Planner):
    def __init__(self, lang="en", top=5000, skip=200):
        self.lang = lang
        self.top = top
        self.skip = skip
        
    def choose_item(
        self, material: List[TeachingItem], context: PlanningContext, time: int
    ):
        return random.choice(material)
    
    def choose_multiple(self, count=10):
        words = top_n_list(self.lang, self.top)[self.skip:]
        return random.sample(words, count)
