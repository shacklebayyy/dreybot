from .base import VerificationProviderInterface
from typing import Dict, Any

class MockVerificationProvider(VerificationProviderInterface):
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return True

    def process_verification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'status': 'MATCH',
            'result': 'VERIFIED',
            'notice': 'DEVELOPMENT MODE: Verification provider is in test mode.',
            'provider': 'Development Mock Provider'
        }
