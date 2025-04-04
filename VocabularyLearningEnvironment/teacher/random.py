from . base import BaseTeacher
import random

class RandomTeacher(BaseTeacher):
    def choose_item(self):
        return random.choice(self.material)
    
    def gets_answer(self, queried_item, answer):
        pass