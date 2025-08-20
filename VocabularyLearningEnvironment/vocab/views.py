from django.shortcuts import render
from django.http import JsonResponse
from components.learners.exp_memory import ExpMemoryLearner
from components.teacher.planners import RandomPlanner 
from .models import Vocabulary

planner = RandomPlanner()
learner = ExpMemoryLearner(0, 0)
word_list = planner.load_chosen_words(10)

def home(request):
    return render(request, "vocab/home.html")

def random_word_view(request):
    chosen_item = planner.choose_item(word_list, context=None, time=0)
    question = chosen_item.get_question()
    translation = chosen_item.get_answer()
    learner.learn(chosen_item, time=0)

    return JsonResponse({"word": question,
                        "translation": translation})


