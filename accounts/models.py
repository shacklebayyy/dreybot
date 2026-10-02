from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    ADMIN = 'ADMIN', 'Admin'
    PRODUCT_MANAGER = 'PRODUCT_MANAGER', 'Product Manager'
    ORDER_MANAGER = 'ORDER_MANAGER', 'Order Manager'
    SUPPORT_AGENT = 'SUPPORT_AGENT', 'Support Agent'
    VERIFICATION_MANAGER = 'VERIFICATION_MANAGER', 'Verification Manager'
    FINANCE_MANAGER = 'FINANCE_MANAGER', 'Finance Manager'
    AUDITOR = 'AUDITOR', 'Auditor'
    CUSTOMER = 'CUSTOMER', 'Customer'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profile')
    telegram_user_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=150, blank=True, default='')
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150, blank=True, default='')
    language = models.CharField(max_length=10, default='en')
    role = models.CharField(max_length=30, choices=UserRole.choices, default=UserRole.CUSTOMER)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonus_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_blocked = models.BooleanField(default=False)
    joined_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['telegram_user_id']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip() or self.username or str(self.telegram_user_id)
        return f"{name} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username or f"User #{self.telegram_user_id}"

    @property
    def total_available_balance(self):
        from decimal import Decimal
        return (self.balance or Decimal('0.00')) + (self.bonus_balance or Decimal('0.00'))

    def deduct_balance(self, amount):
        from decimal import Decimal
        amt = Decimal(str(amount))
        if self.bonus_balance > 0:
            if self.bonus_balance >= amt:
                self.bonus_balance -= amt
                amt = Decimal('0.00')
            else:
                amt -= self.bonus_balance
                self.bonus_balance = Decimal('0.00')
        if amt > 0:
            self.balance -= amt
        self.save()

    def credit_balance(self, amount, bonus_amount=0):
        from decimal import Decimal
        self.balance += Decimal(str(amount))
        if bonus_amount:
            self.bonus_balance += Decimal(str(bonus_amount))
        self.save()

    @property
    def is_admin_role(self):
        return self.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.PRODUCT_MANAGER,
            UserRole.ORDER_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.VERIFICATION_MANAGER,
            UserRole.FINANCE_MANAGER,
            UserRole.AUDITOR
        ]

