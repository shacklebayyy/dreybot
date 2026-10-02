from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_profile', 'action', 'object_type', 'object_id', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'object_type', 'object_id', 'user_profile__username')
