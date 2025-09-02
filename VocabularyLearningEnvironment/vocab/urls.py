from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('user_page/', views.user_page, name="user_page"),
    path('home/', views.home, name="home"),
    path('random-word/', views.random_word_view, name='random_word_by_id'),
    path("login/", views.login_view, name = "login"),
    path("logout/", views.logout_view, name="logout"),
    path('join/', views.join, name="join"),
    path('create_list/<int:count>/', views.create_list, name="create_list"),
    path("delete_list/<int:list_id>/", views.delete_list, name="delete_list"),
    path('submit-answer/', views.submit_answer, name='submit_answer'),
    path("sessions/", views.study_sessions, name="study_sessions"),
    path("sessions/<int:session_id>/start/", views.start_session, name="start_session"),
    path("public-decks/", views.get_public_decks, name="get_public_decks"),
    path("reverse_privacy/<int:deck_id>/", views.reverse_privacy, name="reverse_privacy"),
    path("study/start/", views.start_study_session, name="study_start"),
    path("study/end/", views.end_study_session, name="study_end"),
    path("study/status/", views.get_study_time_status, name="study_status"),
    path("study/update_time/", views.update_study_time, name="study_update_time"),
    path("sessions/<int:session_id>/info/", views.session_info, name="session_info"),

]