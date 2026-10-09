from django.test import TestCase
from accounts.models import UserProfile, UserRole
from accounts.services import get_or_create_telegram_user
from orders.models import Order, PaymentStatus, OrderStatus
from payments.models import Payment, PaymentProviderType, PaymentTransactionStatus
from payments.services import process_payment_confirmation
from verification.models import VerificationService
from catalog.models import Product, Category

class OrderAdminServiceTestCase(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_user_id=123456789, username='testadmin', role=UserRole.SUPER_ADMIN)
        self.category = Category.objects.create(name='Test Category', slug='test-cat')
        self.product = Product.objects.create(name='Test Template', category=self.category, price=10.00, slug='test-template')

    def test_order_status_remains_pending_after_payment_verification(self):
        order = Order.objects.create(
            customer=self.user,
            subtotal=10.00,
            discount=0.00,
            total=10.00,
            currency='USD',
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING
        )
        payment = Payment.objects.create(
            order=order,
            provider=PaymentProviderType.MOCK,
            transaction_reference=order.order_number,
            amount=10.00,
            currency='USD',
            status=PaymentTransactionStatus.PENDING
        )

        success = process_payment_confirmation(payment.transaction_reference)
        self.assertTrue(success)

        order.refresh_from_db()
        self.assertEqual(order.payment_status, PaymentStatus.PAID)
        self.assertEqual(order.order_status, OrderStatus.PENDING)

    def test_admin_role_persistence(self):
        profile = get_or_create_telegram_user(telegram_id=123456789, username='testadmin')
        self.assertTrue(profile.is_admin_role)
        self.assertEqual(profile.role, UserRole.SUPER_ADMIN)

    def test_background_check_service_creation(self):
        bg_svc, created = VerificationService.objects.get_or_create(
            code='background_check',
            defaults={
                'name': 'BACKGROUND CHECK / LIVENESS CHECK',
                'description': 'Authorized $1 background check',
                'price': 1.00,
                'active': True
            }
        )
        self.assertEqual(float(bg_svc.price), 1.00)
        self.assertTrue(bg_svc.active)
