from django.db import models
from django.utils import timezone
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

class Vocabulary(models.Model):
    source_word = models.CharField(max_length=100)
    target_word = models.CharField(max_length=100)

    source_language = models.CharField(max_length=50)
    target_language = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    vocabulary_list = models.ForeignKey(VocabularyList, on_delete=models.CASCADE, related_name="vocabularies")
    
    def __str__(self):
        return self.source_word + "->" + self.target_word
    

class UserAnswer(models.Model):
    question = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    user = models.ForeignKey(Member, on_delete=models.CASCADE)
    given_answer = models.CharField(max_length=100)
    answer_time = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return "User " + str(self.user_id) + " - Question " + str(self.question_id)


class UserMemory(models.Model):
    user = models.OneToOneField('Member', on_delete=models.CASCADE)
    memory_json = models.JSONField(default=dict)  

    def __str__(self):
        return f"Memory of {self.user.username}"

class StudySession(models.Model):
    GOAL_TYPE_CHOICES = [
        ("minutes_per_day", "Minutes per day"),
        ("reviews_per_day", "Reviews per day"),
    ]

    user = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="study_sessions")
    vocabulary_list = models.ForeignKey("VocabularyList", on_delete=models.CASCADE, related_name="study_sessions")
    name = models.CharField(max_length=120) 
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES)
    goal_value = models.PositiveIntegerField(default=20)

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField() 

    memory_json = models.JSONField(default=dict, blank=True) 
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


