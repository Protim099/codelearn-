from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from core.utils import BootstrapMixin
from .models import Profile

User = get_user_model()


class RegisterForm(BootstrapMixin, UserCreationForm):
    ROLE_CHOICES = [(Profile.STUDENT, "Student"), (Profile.INSTRUCTOR, "Instructor")]
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=60, required=True)
    last_name = forms.CharField(max_length=60, required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial=Profile.STUDENT)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # role is restricted to student/instructor by the form choices; admin cannot be self-assigned
            Profile.objects.filter(user=user).update(role=self.cleaned_data["role"])
        return user


class UserUpdateForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class ProfileForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "avatar"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "size") and avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Profile picture must be under 2 MB.")
        return avatar
