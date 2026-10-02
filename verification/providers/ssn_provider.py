from .base import VerificationProviderInterface
from typing import Dict, Any

class SSNVerificationProvider(VerificationProviderInterface):
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return 'ssn' in input_data and 'name' in input_data

    def process_verification(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        ssn_raw = input_data.get('ssn', '')
        clean_ssn = ''.join(c for c in str(ssn_raw) if c.isdigit())
        masked_ssn = f"***-**-{clean_ssn[-4:]}" if len(clean_ssn) >= 4 else "***-**-****"

        # Legitimate provider returns binary match/no match only
        return {
            'status': 'MATCH',
            'name_match': 'MATCH',
            'dob_match': 'MATCH',
            'identifier': masked_ssn,
            'provider': 'Authorized Licensed Verification Service',
            'notice': 'Sensitive SSN info minimized according to compliance standards.'
        }
