import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from catalog.models import Product

def default_expiry():
    return timezone.now() + timedelta(hours=24)

class DownloadToken(models.Model):
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='download_tokens')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    expires_at = models.DateTimeField(default=default_expiry)
    max_downloads = models.PositiveIntegerField(default=5)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DownloadToken {self.token[:8]}... for {self.product.name}"

    @property
    def is_valid(self):
        return (
            self.order.payment_status == 'PAID' and
            timezone.now() < self.expires_at and
            self.download_count < self.max_downloads
        )
