from django.test import TestCase
from accounts.models import UserProfile
from verification.models import VerificationService, VerificationRequestStatus
from verification.services import record_consent, create_verification_request, execute_verification

class VerificationSystemTestCase(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(telegram_user_id=777888999, username='veruser')
        self.service = VerificationService.objects.create(name='EIN Verification', code='ein_verification', price=5.00)

    def test_consent_and_verification_execution(self):
        consent = record_consent(customer=self.user, service=self.service)
        self.assertTrue(consent.consent_given)

        req = create_verification_request(customer=self.user, service=self.service, consent_record=consent)
        self.assertEqual(req.status, VerificationRequestStatus.AWAITING_PAYMENT)

        executed = execute_verification(req, {'business_name': 'Test Corp LLC', 'ein': '12-3456789'})
        self.assertEqual(executed.status, VerificationRequestStatus.COMPLETED)
        self.assertEqual(executed.result.get('status'), 'MATCH')
        self.assertIn('****', executed.result.get('ein'))
