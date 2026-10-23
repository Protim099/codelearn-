from django import forms
from django.core.paginator import Paginator
from django.utils.text import slugify


class BootstrapMixin:
    """Adds Bootstrap 5 classes to every field widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "form-check-input"
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs["class"] = "form-select"
            else:
                w.attrs["class"] = "form-control"


def paginate(request, queryset, per_page=9):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def unique_slug(instance, source, field="slug"):
    base = slugify(source.replace("+", "plus"))[:180] or "item"
    slug, n = base, 2
    Model = instance.__class__
    while Model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug
