from django.contrib import admin
from .models import Vocabulary, Member, VocabularyList, UserAnswer, UserMemory, StudySession, DailyReviewCounter

# Register your models here.
admin.site.register(Vocabulary)
admin.site.register(Member)
admin.site.register(VocabularyList)
admin.site.register(UserAnswer)
admin.site.register(UserMemory)
admin.site.register(StudySession)
admin.site.register(DailyReviewCounter)
