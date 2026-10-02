from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from accounts.services import get_or_create_telegram_user
from verification.models import VerificationService
from verification.services import record_consent, create_verification_request, execute_verification
from telegram_bot.keyboards.inline import get_verification_services_keyboard, get_consent_keyboard

router = Router()

@router.message(F.text == "🔎 VERIFICATION SERVICES")
async def show_verification_services(message: Message):
    services = await sync_to_async(lambda: list(VerificationService.objects.filter(active=True)))()
    text = (
        "🔎 *AUTHORIZED VERIFICATION SERVICES*\n\n"
        "Select the verification check you require.\n"
        "Note: Verification is conducted strictly via authorized third-party programs with required legal consent."
    )
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_verification_services_keyboard(services)
    )

@router.callback_query(F.data.startswith("v_svc:"))
async def cb_verification_selected(call: CallbackQuery):
    service_code = call.data.split(":")[1]
    service = await sync_to_async(lambda: VerificationService.objects.filter(code=service_code).first())()

    if not service:
        await call.answer("Service not found.", show_alert=True)
        return

    text = (
        f"📋 *{service.name}*\n\n"
        f"💰 *Fee:* `${service.price}` {service.currency}\n"
        f"ℹ️ {service.description}\n\n"
        f"=============================\n"
        f"⚖️ *AUTHORIZATION & CONSENT REQUIRED:*\n"
        f"I confirm that I am authorized to request this verification and consent to the processing of required information by the authorized verification provider.\n"
        f"============================="
    )

    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_consent_keyboard(service.code)
    )
    await call.answer()

@router.callback_query(F.data.startswith("v_consent_yes:"))
async def cb_consent_given(call: CallbackQuery):
    service_code = call.data.split(":")[1]

    def process_consent_verif():
        service = VerificationService.objects.filter(code=service_code).first()
        profile = get_or_create_telegram_user(telegram_id=call.from_user.id)

        consent = record_consent(customer=profile, service=service)
        req = create_verification_request(customer=profile, service=service, consent_record=consent)

        sample_input = {
            'name': profile.full_name,
            'ssn': '123-45-6789',
            'business_name': 'Sample Business LLC',
            'ein': '12-3456789'
        }

        executed_req = execute_verification(req, sample_input)
        return service, executed_req, executed_req.result

    service, executed_req, res = await sync_to_async(process_consent_verif)()

    result_text = (
        f"✅ *VERIFICATION COMPLETE*\n\n"
        f"📋 *Request Number:* `{executed_req.verification_number}`\n"
        f"🔎 *Service:* {service.name}\n"
        f"Status: *{executed_req.status}*\n\n"
        f"📊 *VERIFICATION RESULTS:*\n"
        f"• Result: `{res.get('status', 'MATCH')}`\n"
        f"• Name Match: `{res.get('name_match', 'MATCH')}`\n"
        f"• Identifier: `{res.get('identifier', res.get('ein', '***-**-1234'))}`\n"
        f"• Provider: {res.get('provider', 'Authorized Verification Provider')}\n"
        f"• Verified At: {executed_req.completed_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"ℹ️ _{res.get('notice', 'Sensitive fields masked in accordance with compliance controls.')}_"
    )

    await call.message.edit_text(result_text, parse_mode="Markdown")
    await call.answer("Verification completed.", show_alert=True)
