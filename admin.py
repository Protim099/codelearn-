from django.contrib import admin
from .models import Question, Quiz, QuizAttempt


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "pass_mark")
    inlines = [QuestionInline]


admin.site.register(QuizAttempt)
