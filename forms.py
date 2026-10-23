from django import forms

from core.utils import BootstrapMixin
from .models import Question, Quiz


class QuizForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "description", "module", "pass_mark"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class QuestionForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "option_a", "option_b", "option_c", "option_d", "correct_option", "explanation", "order"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2}), "explanation": forms.Textarea(attrs={"rows": 2})}

    def clean(self):
        data = super().clean()
        correct = data.get("correct_option")
        if correct and not data.get(f"option_{correct.lower()}"):
            raise forms.ValidationError("The correct option must have text.")
        return data
