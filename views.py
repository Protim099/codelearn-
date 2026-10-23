from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import can_manage_course
from core.utils import paginate
from courses.models import Enrollment
from .models import Quiz, QuizAttempt
from .services import grade_quiz


def _can_access(user, course):
    return Enrollment.objects.filter(user=user, course=course).exists() or can_manage_course(user, course)


@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("course").prefetch_related("questions"), pk=pk)
    if not _can_access(request.user, quiz.course):
        messages.warning(request, "Enroll in the course to take its quizzes.")
        return redirect(quiz.course.get_absolute_url())
    questions = quiz.questions.all()
    if request.method == "POST":
        if not questions:
            messages.error(request, "This quiz has no questions yet.")
            return redirect(request.path)
        score, total, answers = grade_quiz(quiz, request.POST)
        if len(answers) < total:
            messages.error(request, "Please answer every question before submitting.")
            return render(request, "quizzes/take.html", {"quiz": quiz, "questions": questions, "chosen": request.POST})
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz, score=score, total=total,
                                             percentage=round(score * 100 / total), answers=answers)
        return redirect("quizzes:result", pk=attempt.pk)
    return render(request, "quizzes/take.html", {"quiz": quiz, "questions": questions, "chosen": {}})


@login_required
def result(request, pk):
    attempt = get_object_or_404(QuizAttempt.objects.select_related("quiz__course"), pk=pk)
    if attempt.user_id != request.user.id and not can_manage_course(request.user, attempt.quiz.course):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    rows = []
    for q in attempt.quiz.questions.all():
        chosen = attempt.answers.get(str(q.pk), "")
        rows.append({"q": q, "chosen": chosen, "correct": chosen == q.correct_option,
                     "options": [(k, v, k == q.correct_option, k == chosen) for k, v in q.options]})
    return render(request, "quizzes/result.html", {"attempt": attempt, "rows": rows})


@login_required
def history(request):
    attempts = QuizAttempt.objects.filter(user=request.user).select_related("quiz__course")
    stats = attempts.aggregate(avg=Avg("percentage"), best=Max("percentage"))
    return render(request, "quizzes/history.html", {
        "page": paginate(request, attempts, 15), "stats": stats, "count": attempts.count(),
        "passed": sum(1 for a in attempts if a.passed)})
