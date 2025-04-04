from teacher.items import WordItem
from teacher.base import Teacher
from teacher.planning_contexts import EmptyPlanningContext, FixedHorizonContext
from teacher.planners import RandomPlanner
from learners.exp_memory import ExpMemoryLearner


material = [WordItem("dog", "hund"), 
            WordItem("cat", "katze")]



context = EmptyPlanningContext()
planner = RandomPlanner()
teacher = Teacher(material, planner, context)

learner = ExpMemoryLearner(.8, .1)

for t in range(10):
    item = teacher.choose_item()
    reply = learner.reply(item.get_question(), t)
    learner.learn(item, t)
    teacher.gets_answer(item, reply)
    print("Question:", item.get_question(), " |  Answer:", reply)