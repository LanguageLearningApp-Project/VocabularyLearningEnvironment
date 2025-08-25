from django.contrib import admin
from .models import Vocabulary, Member, VocabularyList, UserAnswer, UserMemory

# Register your models here.
admin.site.register(Vocabulary)
admin.site.register(Member)
admin.site.register(VocabularyList)
admin.site.register(UserAnswer)
admin.site.register(UserMemory)