from django.shortcuts import redirect, render
from django.http import JsonResponse
from components.learners.exp_memory import ExpMemoryLearner
from components.teacher.planners import RandomPlanner 
from .forms import MemberForm
from .models import Member
from django.contrib import messages
from django.shortcuts import redirect

planner = RandomPlanner()
learner = ExpMemoryLearner(0, 0)
word_list = planner.load_chosen_words(10)

def main_page(request):
    return render(request, "vocab/main_page.html")

def home(request):
    return render(request, "vocab/home.html")

def random_word_view(request):
    chosen_item = planner.choose_item(word_list, context=None, time=0)
    question = chosen_item.get_question()
    translation = chosen_item.get_answer()
    learner.learn(chosen_item, time=0)

    return JsonResponse({"word": question,
                        "translation": translation})

def login(request):
    if request.method =="POST":
        user_name = request.POST.get("user_name")
        password = request.POST.get("password")
        try:
            member = Member.objects.get(user_name=user_name, password=password)
            
            request.session["member_id"] = member.id
            request.session["member_username"] = member.user_name

            return render(request, "vocab/home.html",{})
        except:
            messages.error(request, "Invalid username or password.")
            return render(request, "vocab/login.html", {})
            
    else:
        return render (request, "vocab/login.html", {})
    
def logout(request):
    request.session.flush()
    return redirect("main_page") 
                

def join(request):
    if request.method =="POST":
        form = MemberForm(request.POST or None)
        user_name = request.POST.get("user_name")
        if (form.is_valid() and not(Member.objects.filter(user_name=user_name).exists())):
            form.save()
            messages.success(request, "Account created.")
            return redirect("login")
        else:
            messages.error(request, "Username already taken.")
            return redirect("join")
    else:
        return render (request, "vocab/join.html", {})