from abc import ABC, abstractmethod
from typing import Dict, Any

class PaymentProviderInterface(ABC):
    @abstractmethod
    def initialize_payment(self, reference: str, amount: float, currency: str, description: str, customer_email: str = '') -> Dict[str, Any]:
        """
        Initialize payment session with provider.
        Returns dict containing checkout_url or payment instructions, and provider_reference.
        """
        pass

    @abstractmethod
    def verify_payment(self, transaction_reference: str) -> Dict[str, Any]:
        """
        Verify payment status with provider.
        Returns dict with keys: 'success' (bool), 'status' (str), 'raw_response' (dict).
        """
        pass

    @abstractmethod
    def refund_payment(self, transaction_reference: str, amount: float = None) -> Dict[str, Any]:
        """
        Refund payment.
        """
        pass
