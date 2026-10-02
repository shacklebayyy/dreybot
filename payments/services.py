from django.utils import timezone
from orders.models import Order, PaymentStatus, OrderStatus
from .models import Payment, PaymentProviderType, PaymentTransactionStatus
from .providers.base import PaymentProviderInterface
from .providers.stripe_provider import StripePaymentProvider
from .providers.paystack_provider import PaystackPaymentProvider
from .providers.mpesa_provider import MpesaPaymentProvider
from .providers.crypto_provider import CryptoPaymentProvider
from .providers.mock_provider import MockPaymentProvider

def get_payment_provider(provider_type: str) -> PaymentProviderInterface:
    if provider_type == PaymentProviderType.STRIPE:
        return StripePaymentProvider()
    elif provider_type == PaymentProviderType.PAYSTACK:
        return PaystackPaymentProvider()
    elif provider_type == PaymentProviderType.MPESA:
        return MpesaPaymentProvider()
    elif provider_type == PaymentProviderType.CRYPTO:
        return CryptoPaymentProvider()
    else:
        return MockPaymentProvider()

def initialize_order_payment(order: Order, provider_type: str) -> dict:
    provider = get_payment_provider(provider_type)
    ref = order.order_number
    res = provider.initialize_payment(
        reference=ref,
        amount=float(order.total),
        currency=order.currency,
        description=f"DreyDocs Order {order.order_number}"
    )

    if res.get('success'):
        Payment.objects.create(
            order=order,
            provider=provider_type,
            transaction_reference=res.get('provider_reference', ref),
            amount=order.total,
            currency=order.currency,
            status=PaymentTransactionStatus.PENDING,
            raw_response=res.get('raw_response', {})
        )
    return res

def process_payment_confirmation(transaction_reference: str) -> bool:
    """
    Server-side verification of payment before marking order as PAID.
    """
    try:
        payment = Payment.objects.get(transaction_reference=transaction_reference)
    except Payment.DoesNotExist:
        # Check by order_number
        try:
            payment = Payment.objects.filter(order__order_number=transaction_reference).latest('created_at')
        except Payment.DoesNotExist:
            return False

    provider = get_payment_provider(payment.provider)
    verify_res = provider.verify_payment(payment.transaction_reference)

    if verify_res.get('success'):
        payment.status = PaymentTransactionStatus.PAID
        payment.save()

        if payment.order:
            order = payment.order
            order.payment_status = PaymentStatus.PAID
            order.order_status = OrderStatus.COMPLETED
            order.paid_at = timezone.now()
            order.completed_at = timezone.now()
            order.save()

            from downloads.services import generate_download_tokens_for_order
            generate_download_tokens_for_order(order)

            try:
                from notifications.services import notify_admins
                cust = order.customer.first_name or order.customer.username or f"ID:{order.customer.telegram_user_id}"
                notify_admins(
                    f"💰 *ORDER PAYMENT VERIFIED & CONFIRMED*\n\n"
                    f"📋 *Order:* `{order.order_number}`\n"
                    f"👤 *Customer:* `{cust}` (@{order.customer.username or 'N/A'})\n"
                    f"💵 *Amount:* ${order.total:.2f} USD\n"
                    f"⚡ *Status:* COMPLETED / PAID"
                )
            except Exception as e:
                print(f"Failed to send admin payment verification alert: {e}")
        return True
    return False

def process_wallet_payment(order: Order) -> dict:

    from decimal import Decimal
    customer = order.customer
    total_avail = customer.total_available_balance
    if total_avail < order.total:
        shortfall = order.total - total_avail
        return {
            'success': False,
            'reason': 'INSUFFICIENT_FUNDS',
            'required': order.total,
            'available': total_avail,
            'balance': customer.balance,
            'bonus_balance': customer.bonus_balance,
            'shortfall': shortfall
        }

    # Deduct balance
    customer.deduct_balance(order.total)

    # Update Order
    order.payment_status = PaymentStatus.PAID
    order.order_status = OrderStatus.COMPLETED
    order.paid_at = timezone.now()
    order.completed_at = timezone.now()
    order.save()

    # Create Payment record
    Payment.objects.create(
        order=order,
        provider=PaymentProviderType.WALLET,
        transaction_reference=f"WLT-{order.order_number}",
        amount=order.total,
        currency=order.currency,
        status=PaymentTransactionStatus.PAID,
        raw_response={'wallet_deducted': True, 'remaining_balance': str(customer.total_available_balance)}
    )

    from downloads.services import generate_download_tokens_for_order
    tokens = generate_download_tokens_for_order(order)
    token_obj = tokens[0] if tokens else order.download_tokens.first()

    try:
        from notifications.services import notify_admins
        items_str = ", ".join([item.product.name for item in order.items.all()]) or "Document Order"
        cust = customer.first_name or customer.username or f"ID:{customer.telegram_user_id}"
        notify_admins(
            f"💰 *ORDER PAID (WALLET)*\n\n"
            f"📋 *Order:* `{order.order_number}`\n"
            f"👤 *Customer:* `{cust}` (@{customer.username or 'N/A'})\n"
            f"📦 *Item:* {items_str}\n"
            f"💵 *Amount Paid:* ${order.total:.2f} USD\n"
            f"⚡ *Status:* COMPLETED / PAID"
        )
    except Exception as e:
        print(f"Failed to send admin paid notification: {e}")

    return {
        'success': True,
        'order': order,
        'token': token_obj,
        'remaining_balance': customer.total_available_balance
    }

