import random
import string
from django.db import models
from django.utils import timezone
from accounts.models import UserProfile

class VerificationRequestStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
    AWAITING_CONSENT = 'AWAITING_CONSENT', 'Awaiting Consent'
    QUEUED = 'QUEUED', 'Queued'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    REFUNDED = 'REFUNDED', 'Refunded'

def generate_verification_number():
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=5))
    return f"VER-{date_str}-{random_str}"

class VerificationService(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    currency = models.CharField(max_length=5, default='USD')
    active = models.BooleanField(default=True)
    requires_consent = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (${self.price})"

class VerificationProvider(models.Model):
    name = models.CharField(max_length=120)
    provider_type = models.CharField(max_length=50, choices=[('IRS', 'IRS Program'), ('SSA', 'SSA Program'), ('THIRD_PARTY', 'Licensed Third Party'), ('MOCK', 'Mock/Development')])
    api_endpoint = models.URLField(blank=True, default='')
    api_key = models.CharField(max_length=255, blank=True, default='')
    secret = models.CharField(max_length=255, blank=True, default='')
    environment = models.CharField(max_length=20, choices=[('SANDBOX', 'Sandbox/Test'), ('PRODUCTION', 'Production')], default='SANDBOX')
    active = models.BooleanField(default=True)
    test_mode = models.BooleanField(default=True)
    required_fields = models.JSONField(default=list, blank=True)
    timeout = models.IntegerField(default=30)
    retry_count = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.environment})"

class ConsentRecord(models.Model):
    customer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='consents')
    service = models.ForeignKey(VerificationService, on_delete=models.CASCADE)
    consent_given = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(default=timezone.now)
    consent_version = models.CharField(max_length=20, default='v1.0')
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Consent by {self.customer} for {self.service.name} at {self.consent_timestamp}"

class VerificationRequest(models.Model):
    verification_number = models.CharField(max_length=32, unique=True, default=generate_verification_number, db_index=True)
    customer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='verification_requests')
    service = models.ForeignKey(VerificationService, on_delete=models.PROTECT)
    provider = models.ForeignKey(VerificationProvider, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=VerificationRequestStatus.choices, default=VerificationRequestStatus.AWAITING_CONSENT, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    currency = models.CharField(max_length=5, default='USD')
    consent_record = models.ForeignKey(ConsentRecord, on_delete=models.SET_NULL, null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True, help_text="Stores masked/minimized verification response")
    provider_reference = models.CharField(max_length=120, blank=True, default='')
    failure_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Req {self.verification_number} - {self.service.name} ({self.status})"

    def mask_ssn(self, ssn: str) -> str:
        clean = ''.join(c for c in str(ssn) if c.isdigit())
        if len(clean) >= 4:
            return f"***-**-{clean[-4:]}"
        return "***-**-****"
