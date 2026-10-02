from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_reference', 'order', 'provider', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('transaction_reference', 'order__order_number')
