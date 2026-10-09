from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from accounts.services import get_or_create_telegram_user
from verification.models import VerificationService, VerificationRequestStatus
from verification.services import record_consent, create_verification_request
from telegram_bot.keyboards.inline import (
    get_verification_services_keyboard, get_consent_keyboard, get_cancel_request_keyboard
)
from telegram_bot.states import VerificationState
from notifications.services import notify_admins

router = Router()

MENU_NAVIGATION_TEXTS = {
    "CC", "[ CC ]", "/cc", "🔎 VERIFICATION SERVICES", "💰 TOP UP BALANCE", "👤 MY ACCOUNT",
    "📄 ID TEMPLATES", "📄 ID MOCKUPS", "🛂 PASSPORT TEMPLATES", "🛂 PASSPORT MOCKUPS",
    "🚗 DRIVER LICENSE TEMPLATES", "🚗 DRIVER LICENSE MOCKUPS", "🏢 BUSINESS DOCUMENTS",
    "🎓 CERTIFICATES", "📚 OTHER TEMPLATES", "🛒 MY ORDERS", "💬 SUPPORT", "💬 SUPPORT / CONTACT",
    "🎟 COUPONS", "🔍 SEARCH", "🔐 ADMIN CONTROL", "❌ CANCEL REQUEST", "CANCEL", "/cancel", "/start"
}

@router.message(F.text == "🔎 VERIFICATION SERVICES")
async def show_verification_services(message: Message, state: FSMContext = None):
    if state:
        await state.clear()
    services = await sync_to_async(lambda: list(VerificationService.objects.filter(active=True).exclude(code='credit_consult')))()
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

@router.message(F.text.in_({"CC", "/cc"}))
async def handle_cc_direct(message: Message, state: FSMContext):
    service = await sync_to_async(lambda: VerificationService.objects.filter(code='credit_consult').first())()
    if not service:
        service = await sync_to_async(lambda: VerificationService.objects.create(
            name="CC", code="credit_consult", price=20.00, active=True, requires_consent=True
        ))()

    await state.set_state(VerificationState.waiting_for_user_data)
    await state.update_data(service_code=service.code)

    prompt_text = (
        f"✍️ *PLEASE SUBMIT YOUR VERIFICATION DATA*\n\n"
        f"📋 *Service:* {service.name} (${service.price} {service.currency})\n"
        f"⏱ *Turnaround Time:* Order ready within *5 to 30 minutes*\n\n"
        f"Send the data in this format:\n\n"
        f"BIN(EX: 411111)\n"
        f"COUNTRY(EX: USA / UK)\n\n"
        f"_Please reply directly to this message with your details, or click below to cancel._"
    )
    await message.answer(prompt_text, parse_mode="Markdown", reply_markup=get_cancel_request_keyboard())

@router.message(F.text.in_({"❌ CANCEL REQUEST", "CANCEL", "/cancel"}))
async def cancel_verification_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ *Pending verification request cancelled.* You are back in the main menu.", parse_mode="Markdown")
    else:
        await message.answer("No active verification request to cancel.", parse_mode="Markdown")

@router.callback_query(F.data == "v_cancel")
async def cb_cancel_verification_request(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "❌ *Verification request cancelled.* You can select any option from the main menu below.",
        parse_mode="Markdown"
    )
    await call.answer("Request cancelled")

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
        f"⏱ *Turnaround Time:* Order ready within *5 to 30 minutes*\n"
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
async def cb_consent_given(call: CallbackQuery, state: FSMContext):
    service_code = call.data.split(":")[1]
    service = await sync_to_async(lambda: VerificationService.objects.filter(code=service_code).first())()

    if not service:
        await call.answer("Service not found.", show_alert=True)
        return

    await state.set_state(VerificationState.waiting_for_user_data)
    await state.update_data(service_code=service.code)

    if service.code == 'credit_consult':
        format_str = (
            "BIN(EX: 411111)\n"
            "COUNTRY(EX: USA / UK)"
        )
    else:
        format_str = (
            "FIRST NAME (+ middle if any)\n"
            "LAST NAME\n"
            "DOB(EX: MM/DD/YYYY)\n"
            "ADDRESS\n"
            "CITY\n"
            "STATE(EX:CA)\n"
            "ZIP"
        )

    prompt_text = (
        f"✍️ *PLEASE SUBMIT YOUR VERIFICATION DATA*\n\n"
        f"📋 *Service:* {service.name} (${service.price} {service.currency})\n"
        f"⏱ *Turnaround Time:* Order ready within *5 to 30 minutes*\n\n"
        f"Send the data in this format:\n\n"
        f"{format_str}\n\n"
        f"_Please reply directly to this message with your details, or click below to cancel._"
    )

    await call.message.edit_text(prompt_text, parse_mode="Markdown", reply_markup=get_cancel_request_keyboard())
    await call.answer()

@router.message(VerificationState.waiting_for_user_data)
async def process_user_verification_data(message: Message, state: FSMContext):
    raw_data = message.text.strip() if message.text else ""

    # Safety Check: If user typed a command, clicked a menu button, or requested cancellation
    if raw_data.startswith("/") or raw_data in MENU_NAVIGATION_TEXTS:
        await state.clear()
        if raw_data in {"❌ CANCEL REQUEST", "CANCEL", "/cancel"}:
            await message.answer("❌ *Pending verification request cancelled.* You are back in the main menu.", parse_mode="Markdown")
            return
        # If user tapped a main menu button, notify cancellation of pending input
        await message.answer(
            f"⚠️ *Previous pending request cancelled.* Tap *{raw_data}* again to open.",
            parse_mode="Markdown"
        )
        return

    if not raw_data:
        await message.answer("Please reply with your verification data in the requested format or click *❌ CANCEL REQUEST*.", reply_markup=get_cancel_request_keyboard())
        return

    data = await state.get_data()
    service_code = data.get("service_code")

    def submit_verif_req():
        service = VerificationService.objects.filter(code=service_code).first()
        if not service:
            return None, None
        profile = get_or_create_telegram_user(telegram_id=message.from_user.id)
        consent = record_consent(customer=profile, service=service)
        req = create_verification_request(customer=profile, service=service, consent_record=consent)
        req.status = VerificationRequestStatus.PROCESSING
        req.result = {'submitted_data': raw_data}
        req.save()
        return service, req

    service, req = await sync_to_async(submit_verif_req)()
    await state.clear()

    if not req:
        await message.answer("Error: Service context lost. Please select a verification service again.")
        return

    # Notify Customer
    cust_msg = (
        f"✅ *VERIFICATION REQUEST SUBMITTED!*\n\n"
        f"📋 *Request Number:* `{req.verification_number}`\n"
        f"🔎 *Service:* {service.name}\n"
        f"💰 *Fee:* `${service.price}` {service.currency}\n"
        f"⏱ *Turnaround Time:* Ready within *5 to 30 minutes*\n"
        f"⏳ *Status:* PROCESSING / SENT TO ADMIN\n\n"
        f"Thank you! Your verification details have been received and sent to our admin team. Your verification results will be delivered directly to this chat within 5 to 30 minutes."
    )
    await message.answer(cust_msg, parse_mode="Markdown")

    # Notify Admins
    def alert_admins():
        profile = req.customer
        cust_name = profile.first_name or profile.username or f"ID:{profile.telegram_user_id}"
        admin_text = (
            f"🚨 *NEW VERIFICATION REQUEST #{req.verification_number}*\n\n"
            f"👤 *Customer:* `{cust_name}` (@{profile.username or 'N/A'})\n"
            f"🔎 *Service:* {service.name} (${service.price} USD)\n"
            f"⏱ *Turnaround Time:* 5 - 30 Minutes\n\n"
            f"📄 *SUBMITTED VERIFICATION DATA:*\n"
            f"```\n{raw_data}\n```\n\n"
            f"⏳ *Status:* AWAITING ADMIN DELIVERY"
        )
        kb = {
            'inline_keyboard': [
                [{'text': '📤 Send Result to Customer', 'callback_data': f'adm_verif_deliver:{req.id}'}],
                [{'text': '❌ Mark Failed', 'callback_data': f'adm_verif_fail:{req.id}'}]
            ]
        }
        notify_admins(admin_text, reply_markup=kb)

    await sync_to_async(alert_admins)()

