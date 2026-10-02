from django.db import models
from django.utils import timezone
from accounts.models import UserProfile
from orders.models import Order

class DiscountType(models.TextChoices):
    PERCENTAGE = 'PERCENTAGE', 'Percentage'
    FIXED = 'FIXED', 'Fixed Amount'

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        val = f"{self.discount_value}%" if self.discount_type == DiscountType.PERCENTAGE else f"${self.discount_value}"
        return f"{self.code} ({val} OFF)"

    def is_valid(self, subtotal=0.00, customer=None):
        if not self.active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.times_used >= self.usage_limit:
            return False
        if float(subtotal) < float(self.minimum_order):
            return False
        if customer:
            user_count = CouponUsage.objects.filter(coupon=self, customer=customer).count()
            if user_count >= self.per_user_limit:
                return False
        return True

    def calculate_discount(self, subtotal: float) -> float:
        subtotal = float(subtotal)
        if self.discount_type == DiscountType.PERCENTAGE:
            disc = subtotal * (float(self.discount_value) / 100.0)
            if self.maximum_discount and disc > float(self.maximum_discount):
                disc = float(self.maximum_discount)
            return round(disc, 2)
        else:
            return min(subtotal, float(self.discount_value))

class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    customer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} used {self.coupon.code}"
