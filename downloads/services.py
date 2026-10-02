from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import DownloadToken
from orders.models import Order

def generate_download_tokens_for_order(order: Order) -> list:
    expiry_hours = getattr(settings, 'DOWNLOAD_TOKEN_EXPIRY_HOURS', 24)
    expires_at = timezone.now() + timedelta(hours=expiry_hours)
    max_dl = getattr(settings, 'DEFAULT_MAX_DOWNLOADS', 5)

    tokens = []
    for item in order.items.all():
        token = DownloadToken.objects.create(
            order=order,
            product=item.product,
            expires_at=expires_at,
            max_downloads=max_dl
        )
        tokens.append(token)
    return tokens
