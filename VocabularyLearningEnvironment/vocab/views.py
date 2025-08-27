from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from components.teacher.items import WordItem
from components.learners.exp_memory import ExpMemoryLearner
from components.teacher.planners import RandomPlanner 
from .forms import MemberForm
from .models import Member, UserAnswer, UserMemory, Vocabulary, VocabularyList
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
import unicodedata, re
from django.views.decorators.http import require_POST
from django.db import transaction

planner = RandomPlanner()


def _normalize(s: str):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s.casefold()

def main_page(request):
    return render(request, "vocab/main_page.html")

def user_page(request):
    member_id = request.session.get("member_id")
    member = get_object_or_404(Member, id=member_id)
    user_decks = VocabularyList.objects.filter(user=member)
    username = request.session.get("member_username")

    return render(
        request,
        "vocab/user_page.html",
        {"username": username, "user_decks": user_decks}
    )


def home(request):
    return render(request, "vocab/home.html")

def random_word_view(request, deck_id):
    member_id = request.session.get("member_id")
    deck = Vocabulary.objects.filter(vocabulary_list__id=deck_id)
    
    item_list = []
    vocab_dict = {}

    for vocab in deck:
        word_item = WordItem(source = vocab.source_word, target = vocab.target_word)
        item_list.append(word_item)
        vocab_dict[word_item] = vocab

    learner_memory = request.session.get("learner_memory") or {}
    learner = ExpMemoryLearner(alpha=0.1, beta=0.5)
    learner.load_memory(learner_memory)

    chosen_item = planner.choose_item(item_list, context=None, time=0)
    question = chosen_item.get_question()
    translation = chosen_item.get_answer()
    
    chosen_vocab = vocab_dict[chosen_item]

    now_seconds = int(timezone.now().timestamp() )
    learner.learn(chosen_item, time=now_seconds)

    request.session["learner_memory"] = learner.dump_memory()
    member = get_object_or_404(Member, id=member_id)
    user_mem, _ = UserMemory.objects.get_or_create(user=member) 
    user_mem.memory_json = learner.dump_memory()
    user_mem.save()

    return JsonResponse({"word": question, "translation": translation, "question_id": chosen_vocab.id})

def login(request):
    if request.method =="POST":
        user_name = request.POST.get("user_name")
        password = request.POST.get("password")
        try:
            member = Member.objects.get(user_name=user_name, password=password)
            
            request.session["member_id"] = member.id
            request.session["member_username"] = member.user_name

            user_mem, _ = UserMemory.objects.get_or_create(user=member)
            learner = ExpMemoryLearner(alpha=0.1, beta=0.5)
            learner.load_memory(user_mem.memory_json)

            request.session["learner_memory"] = user_mem.memory_json  

            return redirect("user_page")
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
    
def create_list(request, count):
    if request.method == "POST":
        member = Member.objects.get(id=request.session.get("member_id"))
        if member:
            list_name = request.POST.get("list_name")
            description = request.POST.get("description")
            
            new_deck = VocabularyList.objects.create(
                list_name=list_name,
                description=description,
                user=member
            )

            word_items = planner.load_chosen_words(count)
            for item in word_items:
                Vocabulary.objects.create(
                    source_word=item.source,
                    target_word=item.target,
                    source_language="en",
                    target_language="de",
                    vocabulary_list=new_deck
                )
                    
        return redirect("user_page")

def delete_list(request, list_id):
    if request.method == "POST":
        member_id = request.session.get("member_id")

        member = get_object_or_404(Member, id=member_id)
        deck = get_object_or_404(VocabularyList, id=list_id, user=member)
        name = deck.list_name
        deck.delete()

        messages.success(request, f'"{name}" deleted.')

    return redirect("user_page")

def _is_correct(given: str, expected: str) -> bool:
    g = _normalize(given)
    e = _normalize(expected)
    if g == e:
        return True
    # Optional: ignore punctuation for looser matches
    rm = lambda x: re.sub(r"[^\w\s]", "", x)
    return rm(g) == rm(e)

@require_POST
def submit_answer(request):
    user_id = request.session.get("member_id")
    question_id = request.POST.get("question_id")
    given_answer = request.POST.get("given_answer", "")

    if not (user_id and question_id and given_answer):
        return JsonResponse({"status": "error", "message": "Invalid request"})

    try:
        user = Member.objects.get(id=user_id)
        question = Vocabulary.objects.get(id=question_id)
    except Member.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"})
    except Vocabulary.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Question not found"})

    expected = question.target_word  # or .source_word, depending on direction
    correct = _is_correct(given_answer, expected)

    with transaction.atomic():
        user_answer = UserAnswer.objects.create(
            user=user,
            question=question,
            given_answer=given_answer,
            is_correct=correct,
        )

    return JsonResponse({
        "status": "ok",
        "saved_id": user_answer.id,
        "is_correct": correct
    })
