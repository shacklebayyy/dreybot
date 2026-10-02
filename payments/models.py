from django.db import models
from orders.models import Order

class PaymentProviderType(models.TextChoices):
    STRIPE = 'STRIPE', 'Stripe'
    PAYSTACK = 'PAYSTACK', 'Paystack'
    MPESA = 'MPESA', 'M-Pesa'
    CRYPTO = 'CRYPTO', 'Crypto (USDT/BTC)'
    WALLET = 'WALLET', 'Wallet Balance'
    MOCK = 'MOCK', 'Development Mock'


class PaymentTransactionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    provider = models.CharField(max_length=20, choices=PaymentProviderType.choices)
    transaction_reference = models.CharField(max_length=120, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=20, choices=PaymentTransactionStatus.choices, default=PaymentTransactionStatus.PENDING)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_reference} - {self.provider} (${self.amount})"

import random
import string
from django.utils import timezone

def generate_topup_reference():
    date_str = timezone.now().strftime('%Y%m%d')
    rand_str = ''.join(random.choices(string.digits, k=5))
    return f"TPU-{date_str}-{rand_str}"

class TopUpStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved & Credited'
    REJECTED = 'REJECTED', 'Rejected'

class TopUpRequest(models.Model):
    reference = models.CharField(max_length=50, unique=True, default=generate_topup_reference, db_index=True)
    customer = models.ForeignKey('accounts.UserProfile', on_delete=models.CASCADE, related_name='topup_requests')
    currency = models.CharField(max_length=10, default='USDT')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tx_hash = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=TopUpStatus.choices, default=TopUpStatus.PENDING)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TopUp {self.reference} - {self.customer.full_name} (${self.amount})"

