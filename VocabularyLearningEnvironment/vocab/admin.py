from django.contrib import admin
from .models import Vocabulary, Member, VocabularyList, userAnswer, UserMemory

# Register your models here.
admin.site.register(Vocabulary)
admin.site.register(Member)
admin.site.register(VocabularyList)
admin.site.register(userAnswer)
admin.site.register(UserMemory)