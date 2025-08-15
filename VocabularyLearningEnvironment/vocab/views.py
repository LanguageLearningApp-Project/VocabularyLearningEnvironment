from django.shortcuts import render
from django.http import JsonResponse
from components.teacher.planners import RandomPlanner 
from wordfreq import top_n_list

word_list = top_n_list("en", 5000)[200:]

def home(request):
    return render(request, "vocab/home.html")

def random_word_view(request):
    planner = RandomPlanner()
    word = planner.choose_item(word_list, context=None, time=0)
    return JsonResponse({"word": word})
