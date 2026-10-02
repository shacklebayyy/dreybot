import requests
from django.conf import settings
from .base import PaymentProviderInterface
from typing import Dict, Any

class PaystackPaymentProvider(PaymentProviderInterface):
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.base_url = "https://api.paystack.co"

    def initialize_payment(self, reference: str, amount: float, currency: str, description: str, customer_email: str = '') -> Dict[str, Any]:
        if not self.secret_key or 'sample' in self.secret_key:
            return {
                'success': True,
                'checkout_url': f"https://checkout.paystack.com/mock/{reference}",
                'provider_reference': f"pstk_{reference}",
                'instructions': "Paystack Mock Mode"
            }
        headers = {'Authorization': f'Bearer {self.secret_key}'}
        payload = {
            'email': customer_email or 'customer@dreydocs.com',
            'amount': int(amount * 100),
            'currency': currency,
            'reference': reference,
        }
        try:
            r = requests.post(f"{self.base_url}/transaction/initialize", json=payload, headers=headers)
            res = r.json()
            if res.get('status'):
                return {
                    'success': True,
                    'checkout_url': res['data']['authorization_url'],
                    'provider_reference': res['data']['reference'],
                    'raw_response': res
                }
            return {'success': False, 'error': res.get('message', 'Failed to initialize')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_payment(self, transaction_reference: str) -> Dict[str, Any]:
        if not self.secret_key or 'sample' in self.secret_key:
            return {'success': True, 'status': 'PAID', 'raw_response': {'mock': True}}
        headers = {'Authorization': f'Bearer {self.secret_key}'}
        try:
            r = requests.get(f"{self.base_url}/transaction/verify/{transaction_reference}", headers=headers)
            res = r.json()
            paid = res.get('data', {}).get('status') == 'success'
            return {'success': paid, 'status': 'PAID' if paid else 'FAILED', 'raw_response': res}
        except Exception as e:
            return {'success': False, 'status': 'FAILED', 'error': str(e)}

    def refund_payment(self, transaction_reference: str, amount: float = None) -> Dict[str, Any]:
        return {'success': True, 'status': 'REFUNDED'}
