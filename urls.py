from django.urls import path
from . import views

app_name = "quizzes"
urlpatterns = [
    path("quizzes/history/", views.history, name="history"),
    path("quizzes/attempt/<int:pk>/", views.result, name="result"),
    path("quizzes/<int:pk>/", views.take_quiz, name="take"),
]
