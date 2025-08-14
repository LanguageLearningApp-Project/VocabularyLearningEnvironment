from django.db import models

class Vocabulary(models.Model):
    question_word = models.CharField(max_length=100)
    answer_word = models.CharField(max_length=100)

    question_language = models.CharField(max_length=50)
    answer_language = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

def __str__(self):
    return f"{self.question_word} ({self.question_language}) -> {self.answer_word} ({self.answer_language})"
    
class Meta:
    verbose_name = "Vocabulary Word"
    verbose_name_plural = "Vocabulary Words"
