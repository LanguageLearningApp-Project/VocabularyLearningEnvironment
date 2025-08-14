from django.shortcuts import render
from django.http import JsonResponse
from components.teacher.planners import RandomPlanner 

def home(request):
    return render(request, "vocab/home.html")

def random_word_view(request):
    planner = RandomPlanner()
    word = planner.choose_item()
    return JsonResponse({"word": word})
