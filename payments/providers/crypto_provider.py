from django.conf import settings
from .base import PaymentProviderInterface
from typing import Dict, Any

class CryptoPaymentProvider(PaymentProviderInterface):
    def __init__(self):
        self.api_key = getattr(settings, 'CRYPTO_API_KEY', '')
        self.usdt_address = getattr(settings, 'CRYPTO_USDT_ADDRESS', '0x1234567890abcdef1234567890abcdef12345678')

    def initialize_payment(self, reference: str, amount: float, currency: str, description: str, customer_email: str = '') -> Dict[str, Any]:
        return {
            'success': True,
            'checkout_url': f"https://crypto.dreydocs.com/pay/{reference}",
            'provider_reference': f"crypto_{reference}",
            'usdt_address': self.usdt_address,
            'instructions': f"Send {amount} USDT (TRC20 / ERC20) to address:\n`{self.usdt_address}`\nMemo/Ref: `{reference}`"
        }

    def verify_payment(self, transaction_reference: str) -> Dict[str, Any]:
        return {'success': True, 'status': 'PAID', 'raw_response': {'crypto_verified': True}}

    def refund_payment(self, transaction_reference: str, amount: float = None) -> Dict[str, Any]:
        return {'success': True, 'status': 'REFUNDED'}
