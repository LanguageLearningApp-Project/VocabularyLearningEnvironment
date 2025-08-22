from django.urls import path
from . import views
from . views import random_word_view, join, login, logout, user_page

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('user_page/', user_page, name="user_page"),
    path('home/', views.home, name="home"),
    path('random-word/<int:deck_id>/', random_word_view, name='random_word'),
    path("login", login, name = "login"),
    path("logout", logout, name="logout"),
    path('join/', join, name="join"),
    path('create_list/', views.create_list, name="create_list")
]