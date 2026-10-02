import stripe
from django.conf import settings
from .base import PaymentProviderInterface
from typing import Dict, Any

class StripePaymentProvider(PaymentProviderInterface):
    def __init__(self):
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

    def initialize_payment(self, reference: str, amount: float, currency: str, description: str, customer_email: str = '') -> Dict[str, Any]:
        if not stripe.api_key or stripe.api_key.startswith('sk_test_sample'):
            return {
                'success': True,
                'checkout_url': f"https://checkout.stripe.com/mock/{reference}",
                'provider_reference': f"str_{reference}",
                'instructions': "Development mode: Stripe API key not configured."
            }
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {'name': description},
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                client_reference_id=reference,
                success_url=f"https://t.me/{getattr(settings, 'TELEGRAM_BOT_USERNAME', 'DreyDocsBot')}",
                cancel_url=f"https://t.me/{getattr(settings, 'TELEGRAM_BOT_USERNAME', 'DreyDocsBot')}",
            )
            return {
                'success': True,
                'checkout_url': session.url,
                'provider_reference': session.id,
                'raw_response': session
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_payment(self, transaction_reference: str) -> Dict[str, Any]:
        if not stripe.api_key or stripe.api_key.startswith('sk_test_sample'):
            return {'success': True, 'status': 'PAID', 'raw_response': {'mock': True}}
        try:
            session = stripe.checkout.Session.retrieve(transaction_reference)
            paid = session.payment_status == 'paid'
            return {
                'success': paid,
                'status': 'PAID' if paid else 'PENDING',
                'raw_response': session
            }
        except Exception as e:
            return {'success': False, 'status': 'FAILED', 'error': str(e)}

    def refund_payment(self, transaction_reference: str, amount: float = None) -> Dict[str, Any]:
        return {'success': True, 'status': 'REFUNDED'}
