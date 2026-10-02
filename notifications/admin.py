from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'channel', 'title', 'sent', 'sent_at', 'created_at')
    list_filter = ('channel', 'sent', 'created_at')
    search_fields = ('recipient__username', 'recipient__telegram_user_id', 'message')
