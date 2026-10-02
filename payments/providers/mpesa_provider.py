from django.conf import settings
from .base import PaymentProviderInterface
from typing import Dict, Any

class MpesaPaymentProvider(PaymentProviderInterface):
    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '174379')

    def initialize_payment(self, reference: str, amount: float, currency: str, description: str, customer_email: str = '') -> Dict[str, Any]:
        return {
            'success': True,
            'checkout_url': f"https://mpesa.dreydocs.com/pay/{reference}",
            'provider_reference': f"mpesa_{reference}",
            'instructions': f"Send KES {amount} to Paybill {self.shortcode} Account: {reference}"
        }

    def verify_payment(self, transaction_reference: str) -> Dict[str, Any]:
        return {'success': True, 'status': 'PAID', 'raw_response': {'mock': True}}

    def refund_payment(self, transaction_reference: str, amount: float = None) -> Dict[str, Any]:
        return {'success': True, 'status': 'REFUNDED'}
