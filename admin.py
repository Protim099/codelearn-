from django.contrib import admin
from .models import ContactMessage, Notification

admin.site.register(ContactMessage)
admin.site.register(Notification)
