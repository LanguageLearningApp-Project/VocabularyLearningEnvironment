from django.db import models

class Vocabulary(models.Model):
    source_word = models.CharField(max_length=100)
    target_word = models.CharField(max_length=100)

    source_language = models.CharField(max_length=50)
    target_language = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

def __str__(self):
    return f"{self.source_word} ({self.source_language}) -> {self.target_word} ({self.target_language})"
    
class Meta:
    verbose_name = "Vocabulary Word"
    verbose_name_plural = "Vocabulary Words"
