from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from courses.models import Category, Course, Enrollment
from practice.models import CodingExercise
from .forms import ContactForm
from .utils import paginate


def home(request):
    User = get_user_model()
    featured = Course.objects.published().with_stats().order_by("-student_count", "-created_at")[:6]
    context = {
        "featured": featured,
        "categories": Category.objects.all(),
        "stats": {
            "courses": Course.objects.filter(is_published=True).count(),
            "students": User.objects.filter(profile__role="student").count(),
            "instructors": User.objects.filter(profile__role="instructor").count(),
            "enrollments": Enrollment.objects.count(),
        },
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks! Your message has been received.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


def search(request):
    q = request.GET.get("q", "").strip()
    courses, exercises = [], []
    if q:
        courses = Course.objects.published().with_stats().filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q)
            | Q(modules__lessons__title__icontains=q)).distinct()[:30]
        exercises = CodingExercise.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q)).select_related("course")[:30]
    return render(request, "core/search.html", {"q": q, "courses": courses, "exercises": exercises})


@login_required
def notifications(request):
    page = paginate(request, request.user.notifications.all(), 15)
    return render(request, "core/notifications.html", {"page": page})


@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("core:notifications")
