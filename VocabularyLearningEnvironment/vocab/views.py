from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseBadRequest, JsonResponse
from components.teacher.items import WordItem
from components.learners.exp_memory import ExpMemoryLearner
from components.teacher.planners import RandomPlanner 
from .forms import MemberForm, StudySessionForm
from .models import Member, UserAnswer, UserMemory, Vocabulary, VocabularyList, StudySession
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
import unicodedata, re
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth import authenticate, login 
from django.contrib.auth import logout 
from django.contrib.auth.decorators import login_required



planner = RandomPlanner()

def _normalize(s: str):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s.casefold()

def main_page(request):
    return render(request, "vocab/main_page.html")

@login_required
def user_page(request):
    member = request.user
    username = request.user.username
    user_decks = VocabularyList.objects.filter(user=member)
    public_decks = VocabularyList.objects.filter(is_public=True).exclude(user=member)

    if request.method == "POST" and request.POST.get("form_type") == "create_session":
        session_form = StudySessionForm(request.POST, user=member)
        if session_form.is_valid():
            session = session_form.save(commit=False)
            session.user = member
            session.save()
            messages.success(request, "Study session created.")
            return redirect("user_page")
    else:
        session_form = StudySessionForm(user=member)

    sessions = StudySession.objects.filter(user=member).order_by("-created_at")

    return render(
        request,
        "vocab/user_page.html",
        {
            "username": username,
            "user_decks": user_decks,
            "public_decks": public_decks,
            "session_form": session_form,
            "sessions": sessions,
        }
    )

def get_public_decks(request):
    member = request.user
    public_decks = VocabularyList.objects.filter(is_public=True).exclude(user=member)

    decks_data = [
        {
            "id": deck.id,
            "list_name": deck.list_name,
            "description": deck.description,
            "creator": deck.user.username,
        }
        for deck in public_decks
    ]
    return JsonResponse({"decks": decks_data})

def home(request):
    return render(request, "vocab/home.html")

@login_required
def random_word_view(request, deck_id):
    member = request.user
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

    user_mem, _ = UserMemory.objects.get_or_create(user=member) 
    user_mem.memory_json = learner.dump_memory()
    user_mem.save()

    return JsonResponse({"word": question, "translation": translation, "question_id": chosen_vocab.id})

def login_view(request):
    if request.method =="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)  
            messages.success(request, "Welcome back!")
            return redirect("user_page")

        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "vocab/login.html", {})

    else:
        return render (request, "vocab/login.html", {})
    
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("main_page")           

def join(request):
    if request.method == "POST":
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.set_password(form.cleaned_data['password'])
            member.save()
            
            messages.success(request, "Account created.")
            return redirect("login")
        else:
            messages.error(request, "Username already taken or invalid form.")
            return render(request, "vocab/join.html", {"form": form})
    else:
        form = MemberForm()
    return render(request, "vocab/join.html", {"form": form})

@login_required
def create_list(request, count):
    if request.method == "POST":
        member = request.user
        if member:
            list_name = request.POST.get("list_name")
            description = request.POST.get("description")
            is_public = request.POST.get("is_public")

            new_deck = VocabularyList.objects.create(
                list_name=list_name,
                description=description,
                user=member,
                is_public=bool(is_public)
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

@login_required
def delete_list(request, list_id):
    if request.method == "POST":
        member = request.user
        deck = get_object_or_404(VocabularyList, id=list_id, user=member)
        name = deck.list_name
        deck.delete()

        messages.success(request, f'"{name}" deleted.')

    return redirect("user_page")

def _is_correct(given: str, expected: str) -> bool:
    g = _normalize(given)
    e = _normalize(expected)
    
    if not g or g == "":
        return False
          
    if g == e:
        return True
    
    rm = lambda x: re.sub(r"[^\w\s]", "", x)
    return rm(g) == rm(e)

@require_POST
@login_required
def submit_answer(request):
    user = request.user
    question_id = request.POST.get("question_id")
    given_answer = request.POST.get("given_answer", "")

    if not (user and question_id and given_answer):
        return JsonResponse({"status": "error", "message": "Invalid request"})

    try:
        question = Vocabulary.objects.get(id=question_id)
    except Vocabulary.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Question not found"})

    expected = question.target_word  
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

@login_required
def study_sessions(request):
    member = request.user

    if request.method == "POST":
        form = StudySessionForm(request.POST, user=member)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = member
            session.save()
            messages.success(request, "Study session created.")
            return redirect("study_sessions")
    else:
        form = StudySessionForm(user=member)

    sessions = StudySession.objects.filter(user=member).order_by("-created_at")
    return render(request, "vocab/study_sessions.html", {"form": form, "sessions": sessions})

@login_required
def start_session(request, session_id):
    member = request.user
    if not member:
        return HttpResponseBadRequest("Not logged in")

    session = get_object_or_404(StudySession, id=session_id, user=member)

    deck_qs = Vocabulary.objects.filter(vocabulary_list=session.vocabulary_list)
    if not deck_qs.exists():
        return JsonResponse({"status": "error", "message": "This deck is empty."})

    item_list, vocab_map = [], {}
    for vocab in deck_qs:
        wi = WordItem(source=vocab.source_word, target=vocab.target_word)
        item_list.append(wi)
        vocab_map[wi] = vocab

    user_mem, _ = UserMemory.objects.get_or_create(user=member)
    learner = ExpMemoryLearner(alpha=0.1, beta=0.5)
    learner.load_memory(user_mem.memory_json or {})

    now_seconds = int(timezone.now().timestamp())
    chosen_item = planner.choose_item(item_list, context=None, time=now_seconds)
    learner.learn(chosen_item, time=now_seconds)
    
    user_mem.memory_json = learner.dump_memory()
    user_mem.save(update_fields=["memory_json"])

    vocab_obj = vocab_map[chosen_item]
    return JsonResponse({
        "status": "ok",
        "session_id": session.id,
        "word": chosen_item.get_question(),
        "translation": chosen_item.get_answer(),
        "question_id": vocab_obj.id,
    })


@require_POST
@login_required
def submit_answer_session(request):
    user = request.user
    session_id = request.POST.get("session_id")
    question_id = request.POST.get("question_id")
    given_answer = request.POST.get("given_answer", "")

    if not (session_id and question_id):
        return JsonResponse({"status": "error", "message": "Missing parameters"})

    session = get_object_or_404(StudySession, id=session_id, user=user)
    vocab = get_object_or_404(Vocabulary, id=question_id)

    expected = vocab.target_word  
    correct = _is_correct(given_answer, expected)

    user_mem, _ = UserMemory.objects.get_or_create(user=user)
    learner = ExpMemoryLearner(alpha=0.1, beta=0.5)
    learner.load_memory(user_mem.memory_json or {})

    now_seconds = int(timezone.now().timestamp())
    learner.learn(WordItem(vocab.source_word, vocab.target_word), time=now_seconds)

    user_mem.memory_json = learner.dump_memory()
    user_mem.save(update_fields=["memory_json"])

    ua = UserAnswer.objects.create(
        user=user,
        question=vocab,
        given_answer=given_answer,
        is_correct=correct,
    )

    return JsonResponse({
        "status": "ok",
        "saved_id": ua.id,
        "is_correct": correct,
    })

@login_required
def reverse_privacy(request, deck_id):   
    member = request.user

    deck = get_object_or_404(VocabularyList, id=deck_id, user=member)
    deck.is_public = not deck.is_public
    deck.save()
    return redirect('user_page')
