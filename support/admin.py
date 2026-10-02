from django.contrib import admin
from .models import SupportTicket, SupportMessage

class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 1

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'customer', 'subject', 'status', 'assigned_admin', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ticket_number', 'subject', 'customer__username')
    inlines = [SupportMessageInline]
