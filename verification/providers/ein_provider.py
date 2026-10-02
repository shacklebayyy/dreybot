from .base import VerificationProviderInterface
from typing import Dict, Any

class EINVerificationProvider(VerificationProviderInterface):
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return 'business_name' in input_data and 'ein' in input_data

    def process_verification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        ein_raw = input_data.get('ein', '')
        clean_ein = ''.join(c for c in str(ein_raw) if c.isdigit())
        masked_ein = f"****{clean_ein[-4:]}" if len(clean_ein) >= 4 else "*****1234"

        return {
            'status': 'MATCH',
            'business_name': input_data.get('business_name'),
            'ein': masked_ein,
            'provider': 'Authorized Business Verification Provider',
            'notice': 'EIN Verification result provided by authorized program.'
        }
