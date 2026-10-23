from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return "admin"
    return user.profile.role


def user_has_role(user, roles):
    return user_role(user) in roles


def can_manage_course(user, course):
    """Admins manage everything; instructors only their own courses."""
    role = user_role(user)
    return role == "admin" or (role == "instructor" and course.instructor_id == user.id)


def role_required(*roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if user_has_role(request.user, roles):
                return view(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator
