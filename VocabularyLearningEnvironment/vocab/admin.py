from django.contrib import admin
from .models import Vocabulary, Member, VocabularyList, userAnswer

# Register your models here.
admin.site.register(Vocabulary)
admin.site.register(Member)
admin.site.register(VocabularyList)
admin.site.register(userAnswer)