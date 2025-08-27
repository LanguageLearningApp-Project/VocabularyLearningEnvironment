from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('user_page/', views.user_page, name="user_page"),
    path('home/', views.home, name="home"),
    path('random-word/<int:deck_id>/', views.random_word_view, name='random_word_by_id'),
    path("login/", views.login, name = "login"),
    path("logout/", views.logout, name="logout"),
    path('join/', views.join, name="join"),
    path('create_list/<int:count>/', views.create_list, name="create_list"),
    path("delete_list/<int:list_id>/", views.delete_list, name="delete_list"),
    path('submit-answer/', views.submit_answer, name='submit_answer'),
    path("sessions/", views.study_sessions, name="study_sessions"),
    path("sessions/<int:session_id>/start/", views.start_session, name="start_session"),
    path("sessions/submit/", views.submit_answer_session, name="submit_answer_session"),
]