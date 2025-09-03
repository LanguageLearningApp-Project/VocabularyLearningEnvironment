from django.db import models
from django.utils import timezone
from django.db.models import F, Q
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class Member(AbstractUser):
    pass
    
class VocabularyList(models.Model):
    list_name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="vocabulary_lists")
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.list_name
    
class QuizList(models.Model):
    quiz_name = models.CharField(max_length=100)
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="quiz_lists")

    def __str__(self):
        return self.quiz_name

class Vocabulary(models.Model):
    source_word = models.CharField(max_length=100)
    target_word = models.CharField(max_length=100)

    source_language = models.CharField(max_length=50)
    target_language = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    vocabulary_list = models.ForeignKey(VocabularyList, on_delete=models.CASCADE, related_name="vocabularies")
    quiz_list = models.ForeignKey(QuizList, on_delete=models.CASCADE, related_name="quizzes", null=True, blank=True, default=None )
    
    def __str__(self):
        return self.source_word + "->" + self.target_word
    

class UserAnswer(models.Model):
    question = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    given_answer = models.CharField(max_length=100)
    answer_time = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return "User " + str(self.user.username) + " - Question " + str(self.question_id)


class UserMemory(models.Model):
    user = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="word_memories")
    vocabulary = models.ForeignKey("Vocabulary", on_delete=models.CASCADE, null=True)
    vocabulary_list = models.ForeignKey("VocabularyList", on_delete=models.CASCADE, related_name="user_memories")
    n_occurrences = models.IntegerField(default=0)
    last_occurrence = models.IntegerField(default=0)    
    alpha = models.FloatField(default=0.1)
    beta = models.FloatField(default=0.5)

    class Meta:
        unique_together = ("user", "vocabulary", "vocabulary_list")  
        indexes = [
            models.Index(fields=["user", "vocabulary"]),
        ]

    def __str__(self):
        return f"User:{self.user.username} Word:{self.vocabulary.source_word} "

class StudySession(models.Model):
    GOAL_TYPE_CHOICES = [
        ("minutes_per_day", "Minutes per day"),
        ("reviews_per_day", "Reviews per day"),
        ("quiz", "Quiz")
    ]

    user = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="study_sessions")
    vocabulary_list = models.ForeignKey("VocabularyList", on_delete=models.CASCADE, related_name="study_sessions")
    name = models.CharField(max_length=120) 
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    goal_value = models.PositiveIntegerField(default=20)

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField() 
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def days_total(self):
        return (self.end_date - self.start_date).days + 1

    def is_running_today(self):
        today = timezone.localdate()
        return self.is_active and self.start_date <= today <= self.end_date

    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
class DailyReviewCounter(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="daily_review_counters")
    study_session = models.ForeignKey("StudySession", on_delete=models.CASCADE, related_name="daily_review_counters")
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint( #updating the row to not create duplicates
                fields=["user", "date", "study_session"],
                name="uniq_user_date_session_reviews",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["study_session", "date"]),
        ]

    def __str__(self):
        return f"{self.user.username} • {self.date} • {self.study_session_id} • {self.count}"

class DailyMinuteCounter(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="daily_minute_counters")
    study_session = models.ForeignKey("StudySession", on_delete=models.CASCADE, related_name="daily_minute_counters")
    date = models.DateField()
    minutes = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint( #only one active session per user
                fields=["user", "date", "study_session"],
                name="uniq_user_date_session_minutes",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["study_session", "date"]),
        ]

    def __str__(self):
        scope = self.study_session_id or "-"
        return f"{self.user.username} • {self.date} • {scope} • {self.minutes}min"


class ActiveStudySession(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="active_sessions")
    study_session = models.ForeignKey("StudySession", on_delete=models.CASCADE, related_name="active_sessions")
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user"], name="uniq_active_session_per_user"),
        ]
        indexes = [models.Index(fields=["user", "started_at"])]

    def get_elapsed_minutes(self):
        from django.utils import timezone
        elapsed = timezone.now() - self.started_at
        return int(elapsed.total_seconds() / 60)
    
    
    