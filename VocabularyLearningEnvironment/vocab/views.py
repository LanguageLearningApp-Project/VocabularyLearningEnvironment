from django.shortcuts import render
from django.http import JsonResponse
from components.learners.exp_memory import ExpMemoryLearner
from components.teacher.planners import RandomPlanner 
from .forms import MemberForm
from django.contrib import messages

planner = RandomPlanner()
learner = ExpMemoryLearner(0, 0)
word_list = planner.load_chosen_words(10)

def home(request):
    return render(request, "vocab/home.html")

def join(request):
    if request.method =="POST":
        form = MemberForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created.")
        return render(request, "vocab/home.html",{})
    else:
        return render (request, "vocab/join.html", {})

def random_word_view(request):
    chosen_item = planner.choose_item(word_list, context=None, time=0)
    question = chosen_item.get_question()
    translation = chosen_item.get_answer()
    learner.learn(chosen_item, time=0)

    return JsonResponse({"word": question,
                        "translation": translation})


