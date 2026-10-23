from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, RegisterForm, UserUpdateForm


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboards:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to CodeLearn, {user.first_name}!")
        return redirect("dashboards:home")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    uform = UserUpdateForm(request.POST or None, instance=request.user)
    pform = ProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == "POST" and uform.is_valid() and pform.is_valid():
        uform.save()
        pform.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"uform": uform, "pform": pform})
