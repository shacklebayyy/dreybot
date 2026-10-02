from .base import PaymentProviderInterface
from typing import Dict, Any

class MockPaymentProvider(PaymentProviderInterface):
    def initialize_payment(self, reference: str, amount: float, currency: str, description: str, customer_email: str = '') -> Dict[str, Any]:
        return {
            'success': True,
            'checkout_url': f"https://dreydocs.local/mock-pay/{reference}",
            'provider_reference': f"mock_tx_{reference}",
            'instructions': "Click link or proceed to test instant payment confirmation."
        }

    def verify_payment(self, transaction_reference: str) -> Dict[str, Any]:
        return {
            'success': True,
            'status': 'PAID',
            'raw_response': {'mock': True, 'verified': True}
        }

    def refund_payment(self, transaction_reference: str, amount: float = None) -> Dict[str, Any]:
        return {'success': True, 'status': 'REFUNDED'}
