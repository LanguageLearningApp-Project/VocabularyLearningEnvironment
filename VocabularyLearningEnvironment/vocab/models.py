from django.db import models

class VocabularyList(models.Model):
    list_name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    user_id = models.IntegerField(default=0)


    def __str__(self):
        return self.list_name

class Vocabulary(models.Model):
    source_word = models.CharField(max_length=100)
    target_word = models.CharField(max_length=100)

    source_language = models.CharField(max_length=50)
    target_language = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    vocabulary_list_id = models.IntegerField(default=0)
    
    def __str__(self):
        return self.source_word + "->" + self.target_word
    
class Member(models.Model):
    user_name = models.CharField(max_length=100)
    password = models.CharField(max_length=50)
    
    def __str__(self):
        return self.user_name


class userAnswer(models.Model):
    question_id = models.IntegerField(default=0)
    user_id = models.IntegerField(default=0)
    given_answer = models.CharField(max_length=100)
    answer_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "User " + str(self.user_id) + " - Question " + str(self.question_id)


class UserMemory(models.Model):
    user = models.OneToOneField('Member', on_delete=models.CASCADE)
    memory_json = models.JSONField(default=dict)  

    def __str__(self):
        return f"Memory of {self.user.user_name}"

