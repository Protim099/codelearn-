from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from core.models import TimeStampedModel
from courses.models import Course, Module


class Quiz(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name="quizzes")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    pass_mark = models.PositiveIntegerField(default=50, validators=[MinValueValidator(1), MaxValueValidator(100)],
                                            help_text="Passing percentage")

    class Meta:
        verbose_name_plural = "quizzes"
        ordering = ["course", "id"]

    def get_absolute_url(self):
        return reverse("quizzes:take", args=[self.pk])

    def __str__(self):
        return self.title


class Question(models.Model):
    OPTIONS = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    correct_option = models.CharField(max_length=1, choices=OPTIONS)
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    @property
    def options(self):
        pairs = [("A", self.option_a), ("B", self.option_b), ("C", self.option_c), ("D", self.option_d)]
        return [(k, v) for k, v in pairs if v]

    def __str__(self):
        return self.text[:60]


class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    percentage = models.PositiveIntegerField()
    answers = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def passed(self):
        return self.percentage >= self.quiz.pass_mark
