from django.db import transaction
from django.utils import timezone
from accounts.models import UserProfile
from catalog.models import Product
from .models import Order, OrderItem, Cart, PaymentStatus, OrderStatus

def create_order_from_product(customer: UserProfile, product: Product, coupon=None) -> Order:
    with transaction.atomic():
        price = product.current_price
        subtotal = price
        discount = 0.00
        if coupon and coupon.is_valid():
            discount = coupon.calculate_discount(subtotal)
        total = max(0.00, float(subtotal) - float(discount))

        order = Order.objects.create(
            customer=customer,
            subtotal=subtotal,
            discount=discount,
            total=total,
            currency=product.currency,
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING,
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price=price,
            quantity=1
        )

        return order

def create_order_from_cart(customer: UserProfile, coupon=None) -> Order:
    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(customer=customer)
        items = cart.items.select_related('product').all()
        if not items:
            raise ValueError("Cart is empty.")

        subtotal = sum(item.subtotal for item in items)
        discount = 0.00
        if coupon and coupon.is_valid():
            discount = coupon.calculate_discount(subtotal)
        total = max(0.00, float(subtotal) - float(discount))

        order = Order.objects.create(
            customer=customer,
            subtotal=subtotal,
            discount=discount,
            total=total,
            currency=items[0].product.currency,
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.current_price,
                quantity=item.quantity
            )

        # Clear cart
        cart.items.all().delete()
        return order
