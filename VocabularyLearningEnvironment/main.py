from teacher.items import WordItem
from teacher.random import RandomTeacher
from learners.exp_memory import ExpMemoryLearner


material = [WordItem("dog", "hund"), 
            WordItem("cat", "katze")]

teacher = RandomTeacher(material)

learner = ExpMemoryLearner(.8, .1)

for t in range(10):
    item = teacher.choose_item()
    learner.reply(item.get_question(), t)
    learner.learn(item, t)