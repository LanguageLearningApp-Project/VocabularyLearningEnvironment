import time
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseBadRequest, JsonResponse
from components.teacher.items import WordItem
from components.learners.exp_memory import ExpMemoryLearner
from components.teacher.planners import RandomPlanner 
from .forms import MemberForm, StudySessionForm
from .models import Member, UserAnswer, UserMemory, Vocabulary, VocabularyList, StudySession, DailyReviewCounter, ActiveStudySession, DailyMinuteCounter
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
import unicodedata, re
from django.views.decorators.http import require_POST
from django.db import OperationalError, transaction
from django.db.models import F
from django.contrib.auth import authenticate, login 
from django.contrib.auth import logout 
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.views.decorators.csrf import ensure_csrf_cookie


planner = RandomPlanner()

@login_required
def session_info(request, session_id):
    s = get_object_or_404(StudySession, id=session_id, user=request.user)
    return JsonResponse({"goal_type": s.goal_type})

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

@ensure_csrf_cookie
def home(request):
    return render(request, "vocab/home.html")

def choose_random_word(user, session):
    deck = session.vocabulary_list
    vocab_qs = Vocabulary.objects.filter(vocabulary_list=deck)

    if not vocab_qs.exists():
        return {"status": "error", "message": "This deck is empty."}

    item_list = []
    vocab_dict = {}
    
    for vocab in vocab_qs:
        word_item = WordItem(source = vocab.source_word, target = vocab.target_word)
        item_list.append(word_item)
        vocab_dict[word_item] = vocab

    chosen_item = planner.choose_item(item_list, context=None, time=0)
    chosen_vocab = vocab_dict[chosen_item]
    question = chosen_item.get_question()
    translation = chosen_item.get_answer()
    
    now_seconds = int(timezone.now().timestamp() )
    learner = ExpMemoryLearner.load_memory_from_db(user, alpha=0.1, beta=0.5)
    learner.learn(chosen_item, chosen_vocab.id, now_seconds)
   
    learner.save_memory_to_db_with_retry(user)

    return {  
            "word": question,
            "translation": translation,
            "question_id": chosen_vocab.id
        }

@login_required
def random_word_view(request):
    member = request.user
    session_id = request.GET.get("session_id")
    if not session_id:
        return JsonResponse({"status": "error", "message": "session_id is required."})
 
    session = get_object_or_404(
        StudySession.objects.select_related("vocabulary_list"),
        id=session_id,
        user=member
    )
     
    data=choose_random_word(member, session)
    return JsonResponse(data) 


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

            word_items = planner.load_chosen_words(count, user=member)
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

    if not (user and question_id):
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
    session = get_object_or_404(StudySession, id=session_id, user=member)

    data = choose_random_word(member, session)
    
    if not session.is_running_today():
        return JsonResponse(
        {"status": "error", "message": "This study session has ended or has not started yet."},
        status=400
    )
    
    if session.goal_type == "reviews_per_day":
        today = timezone.localdate()
        counter, _ = DailyReviewCounter.objects.get_or_create(
            user=member,
            study_session=session,
            date=today,
            defaults={"count": 0},
        )
        DailyReviewCounter.objects.filter(pk=counter.pk).update(
            count=F("count") + 1
    )
    has_words = Vocabulary.objects.filter(vocabulary_list=session.vocabulary_list).exists()
    if not has_words:
        return JsonResponse({"status": "error", "message": "This deck is empty."})
    return JsonResponse(data)


@login_required
def reverse_privacy(request, deck_id):   
    member = request.user

    deck = get_object_or_404(VocabularyList, id=deck_id, user=member)
    deck.is_public = not deck.is_public
    deck.save()
    return redirect('user_page')

@require_POST
@login_required
@transaction.atomic
def start_study_session(request):
    sid = request.POST.get("study_session_id")
    if not sid:
        return HttpResponseBadRequest("study_session_id is required")

    session = get_object_or_404(StudySession, id=sid, user=request.user)
    
    if session.goal_type != "minutes_per_day":
        ActiveStudySession.objects.filter(user=request.user).delete()
        return JsonResponse({"status": "skipped", "reason": "not_minutes_goal"})

    ActiveStudySession.objects.filter(user=request.user).delete()
    active = ActiveStudySession.objects.create(
        user=request.user,
        study_session=session,
    )
    return JsonResponse({
        "status": "started",
        "session_id": active.id,
        "started_at": active.started_at.isoformat(),
    })

@require_POST
@login_required
@transaction.atomic
def end_study_session(request):
    active = (ActiveStudySession.objects
              .select_for_update()
              .filter(user=request.user)
              .select_related("study_session")
              .first())
    if not active:
        return JsonResponse({"status": "ended", "minutes_studied": 0})
    
    if active.study_session.goal_type != "minutes_per_day":
        active.delete()
        return JsonResponse({"status": "ended", "minutes_studied": 0})

    elapsed_sec = int((timezone.now() - active.started_at).total_seconds())
    full_minutes = elapsed_sec // 60 

    if full_minutes > 0:
        today = timezone.localdate()
        counter, _ = DailyMinuteCounter.objects.select_for_update().get_or_create(
            user=request.user,
            study_session=active.study_session,
            date=today,
            defaults={"minutes": 0},
        )
        DailyMinuteCounter.objects.filter(pk=counter.pk).update(
            minutes=F("minutes") + full_minutes
        )

    active.delete()

    return JsonResponse({"status": "ended", "minutes_studied": int(full_minutes)})

@login_required
def get_study_time_status(request):
    active = ActiveStudySession.objects.filter(user=request.user).first()
    if not active:
        return JsonResponse({"active": False})

    elapsed_sec = int((timezone.now() - active.started_at).total_seconds())
    return JsonResponse({
        "active": True,
        "started_at": active.started_at.isoformat(),
        "elapsed_seconds": elapsed_sec,
        "elapsed_minutes": elapsed_sec // 60,
    })

def update_study_time(request):
    active = (ActiveStudySession.objects
              .select_for_update()
              .filter(user=request.user)
              .select_related("study_session")
              .first())
    if not active:
        return JsonResponse({"active": False})
    
    if active.study_session.goal_type != "minutes_per_day":
        return JsonResponse({"active": True, "added_minutes": 0, "ignored": True})

    elapsed_sec = int((timezone.now() - active.started_at).total_seconds())
    full_minutes = elapsed_sec // 60
    if full_minutes <= 0:
        return JsonResponse({"active": True, "added_minutes": 0})

    today = timezone.localdate()
    counter, _ = DailyMinuteCounter.objects.select_for_update().get_or_create(
        user=request.user,
        study_session=active.study_session,
        date=today,
        defaults={"minutes": 0},
    )
    DailyMinuteCounter.objects.filter(pk=counter.pk).update(
        minutes=F("minutes") + full_minutes
    )

    active.started_at = active.started_at + timedelta(minutes=full_minutes)
    active.save(update_fields=["started_at"])

    return JsonResponse({"active": True, "added_minutes": full_minutes})

@require_POST
@login_required
def delete_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)

    active = (ActiveStudySession.objects
              .select_for_update()
              .filter(user=request.user, study_session=session)
              .first())
    if active:
        if session.goal_type == "minutes_per_day":
            elapsed_sec = int((timezone.now() - active.started_at).total_seconds())
            full_minutes = elapsed_sec // 60
            if full_minutes > 0:
                today = timezone.localdate()
                counter, _ = DailyMinuteCounter.objects.select_for_update().get_or_create(
                    user=request.user,
                    study_session=session,
                    date=today,
                    defaults={"minutes": 0},
                )
                DailyMinuteCounter.objects.filter(pk=counter.pk).update(
                    minutes=F("minutes") + full_minutes
                )
        active.delete()
    session.delete()
    return redirect("user_page")

@login_required
def progress_check(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    today = timezone.localdate()

    if session.goal_type == "reviews_per_day":
        counter = DailyReviewCounter.objects.filter(
            user=request.user, study_session=session, date=today
        ).first()
        progress = counter.count if counter else 0
    else: 
        counter = DailyMinuteCounter.objects.filter(
            user=request.user, study_session=session, date=today
        ).first()
        progress = counter.minutes if counter else 0

    return JsonResponse({
        "goal_type": session.goal_type,
        "goal_value": session.goal_value,
        "progress": progress,
        "done": progress >= session.goal_value,
        "is_running_today": session.is_running_today(),
    })
