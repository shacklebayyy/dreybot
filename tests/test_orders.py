from django.test import TestCase
from accounts.models import UserProfile
from catalog.models import Category, Product
from orders.models import Order, PaymentStatus, OrderStatus
from orders.services import create_order_from_product

class OrderSystemTestCase(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_user_id=111222333, username='testuser')
        self.category = Category.objects.create(name='ID Mockups', slug='id-mockups')
        self.product = Product.objects.create(
            name='Test ID Mockup',
            slug='test-id-mockup',
            category=self.category,
            price=12.00
        )

    def test_create_order_from_product(self):
        order = create_order_from_product(customer=self.user, product=self.product)
        self.assertIsNotNone(order.order_number)
        self.assertTrue(order.order_number.startswith('DRD-'))
        self.assertEqual(order.total, 12.00)
        self.assertEqual(order.payment_status, PaymentStatus.PENDING)
        self.assertEqual(order.items.count(), 1)
