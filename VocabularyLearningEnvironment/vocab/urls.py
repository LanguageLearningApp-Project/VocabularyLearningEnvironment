from django.urls import path
from . import views
from . views import random_word_view, join

urlpatterns = [
    path('main_page/', views.main_page, name='main_page'),
    path('home/', views.home, name="home"),
    path('random-word/', random_word_view, name='random_word'),
    path('join/', join, name="join"),

]