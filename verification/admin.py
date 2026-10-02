from django.contrib import admin
from .models import VerificationService, VerificationProvider, ConsentRecord, VerificationRequest

@admin.register(VerificationService)
class VerificationServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'currency', 'active', 'requires_consent')
    list_filter = ('active', 'requires_consent')

@admin.register(VerificationProvider)
class VerificationProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_type', 'environment', 'active', 'test_mode')
    list_filter = ('provider_type', 'environment', 'active')

@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'consent_given', 'consent_timestamp')
    list_filter = ('consent_given', 'consent_timestamp')

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('verification_number', 'customer', 'service', 'status', 'price', 'created_at')
    list_filter = ('status', 'service', 'created_at')
    search_fields = ('verification_number', 'customer__username', 'customer__telegram_user_id')
