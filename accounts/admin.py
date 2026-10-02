from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('telegram_user_id', 'username', 'first_name', 'last_name', 'role', 'is_blocked', 'joined_at')
    list_filter = ('role', 'is_blocked', 'joined_at')
    search_fields = ('telegram_user_id', 'username', 'first_name', 'last_name')
