from teaching.items import WordItem
from teaching.teaching import RandomTeacher
from ExpMemoryLearner.learner import ExpMemoryLearner


material = [WordItem("dog", "hund"), 
            WordItem("cat", "katze")]

teacher = RandomTeacher(material)

learner = ExpMemoryLearner(.8, .1)

for t in range(10):
    item = teacher.choose_item()
    learner.reply(item.get_question(), t)
    learner.learn(item, t)