from accounts.permissions import user_role


def site_globals(request):
    ctx = {"site_name": "CodeLearn", "role": user_role(request.user)}
    if request.user.is_authenticated:
        ctx["unread_count"] = request.user.notifications.filter(is_read=False).count()
    return ctx
