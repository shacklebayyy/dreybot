from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile
from catalog.models import Category, Product
from orders.models import Order, PaymentStatus, OrderStatus
from downloads.models import DownloadToken
from downloads.services import generate_download_tokens_for_order

class SecureDownloadTestCase(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_user_id=444555666)
        self.category = Category.objects.create(name='Certificates', slug='certificates')
        self.product = Product.objects.create(name='Sample Cert', slug='sample-cert', category=self.category, price=10.00)
        self.order = Order.objects.create(customer=self.user, total=10.00, payment_status=PaymentStatus.PAID, order_status=OrderStatus.COMPLETED)
        self.order.items.create(product=self.product, price=10.00, quantity=1)

    def test_download_token_generation_and_validation(self):
        tokens = generate_download_tokens_for_order(self.order)
        self.assertEqual(len(tokens), 1)
        token = tokens[0]
        self.assertTrue(token.is_valid)

        # Unpaid order should render token invalid
        self.order.payment_status = PaymentStatus.PENDING
        self.order.save()
        self.assertFalse(token.is_valid)

    def test_expired_token(self):
        token = DownloadToken.objects.create(
            order=self.order,
            product=self.product,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        self.assertFalse(token.is_valid)
