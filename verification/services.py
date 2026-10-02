from django.utils import timezone
from accounts.models import UserProfile
from audit.utils import log_audit
from .models import (
    VerificationService, VerificationProvider, ConsentRecord,
    VerificationRequest, VerificationRequestStatus
)
from .providers.ssn_provider import SSNVerificationProvider
from .providers.ein_provider import EINVerificationProvider
from .providers.mock_provider import MockVerificationProvider

def record_consent(customer: UserProfile, service: VerificationService, ip_address: str = None) -> ConsentRecord:
    return ConsentRecord.objects.create(
        customer=customer,
        service=service,
        consent_given=True,
        consent_timestamp=timezone.now(),
        consent_version='v1.0',
        ip_address=ip_address
    )

def create_verification_request(customer: UserProfile, service: VerificationService, consent_record: ConsentRecord) -> VerificationRequest:
    return VerificationRequest.objects.create(
        customer=customer,
        service=service,
        status=VerificationRequestStatus.AWAITING_PAYMENT,
        price=service.price,
        currency=service.currency,
        consent_record=consent_record
    )

def execute_verification(req: VerificationRequest, input_data: dict) -> VerificationRequest:
    if not req.consent_record or not req.consent_record.consent_given:
        req.status = VerificationRequestStatus.FAILED
        req.failure_reason = "Consent not provided."
        req.save()
        return req

    req.status = VerificationRequestStatus.PROCESSING
    req.submitted_at = timezone.now()
    req.save()

    # Determine provider interface
    if req.service.code == 'ssn_verification':
        provider_impl = SSNVerificationProvider()
    elif req.service.code in ['ein_verification', 'business_registration']:
        provider_impl = EINVerificationProvider()
    else:
        provider_impl = MockVerificationProvider()

    res = provider_impl.process_verification(input_data)

    req.status = VerificationRequestStatus.COMPLETED
    req.completed_at = timezone.now()
    req.result = res
    req.save()

    log_audit(
        user_profile=req.customer,
        action='VERIFICATION_COMPLETED',
        object_type='VerificationRequest',
        object_id=req.verification_number,
        metadata={'service': req.service.code, 'status': req.status}
    )

    return req
