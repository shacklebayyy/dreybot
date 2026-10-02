from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from accounts.services import get_or_create_telegram_user
from support.models import SupportTicket, SupportMessage
from orders.models import Order, PaymentStatus, OrderStatus
from telegram_bot.states import SupportState, CustomRequestState
from telegram_bot.keyboards.inline import get_payment_methods_keyboard

router = Router()

@router.message(F.text == "💬 SUPPORT")
async def show_support(message: Message, state: FSMContext):
    def fetch_support():
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )
        return profile, SupportTicket.objects.filter(customer=profile, status__in=['OPEN', 'IN_PROGRESS']).count()

    profile, open_tickets = await sync_to_async(fetch_support)()
    await state.set_state(SupportState.waiting_for_message)

    text = (
        f"💬 *DREYDOCS SUPPORT & HELP DESK*\n\n"
        f"Need assistance with your orders, document templates, or custom requests?\n\n"
        f"• Active Open Tickets: *{open_tickets}*\n"
        f"• Support Desk: *Admin Ticket System*\n\n"
        f"✍️ *Please type your support message or request directly below in this chat to open an Admin Ticket:*"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Custom Order Request", callback_data="custom_req_prompt")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data == "ticket_prompt")
async def cb_ticket_prompt(call: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_for_message)
    await call.message.answer(
        "📝 *TYPE YOUR SUPPORT MESSAGE*\n\nPlease type your question or issue directly below in this chat:",
        parse_mode="Markdown"
    )
    await call.answer()

from notifications.services import notify_admins

def notify_ticket_created(ticket, message_text):
    cust = ticket.customer.first_name or ticket.customer.username or f"ID:{ticket.customer.telegram_user_id}"
    text = (
        f"🚨 *NEW SUPPORT TICKET #{ticket.ticket_number}*\n\n"
        f"👤 *Customer:* `{cust}` (@{ticket.customer.username or 'N/A'})\n"
        f"💬 *Message:* _{message_text}_\n"
        f"⏳ *Status:* OPEN"
    )
    kb = {
        'inline_keyboard': [
            [{'text': '💬 Reply to Ticket', 'callback_data': f'adm_reply_tck:{ticket.id}'}],
            [{'text': '✅ Close Ticket', 'callback_data': f'adm_close_tck:{ticket.id}'}]
        ]
    }
    notify_admins(text, reply_markup=kb)

def notify_custom_order_created(order, req_notes):
    cust = order.customer.first_name or order.customer.username or f"ID:{order.customer.telegram_user_id}"
    text = (
        f"🚨 *NEW CUSTOM ORDER REQUEST #{order.order_number}*\n\n"
        f"👤 *Customer:* `{cust}` (@{order.customer.username or 'N/A'})\n"
        f"📝 *Requirements:* _{req_notes}_\n"
        f"💰 *Fee:* ${order.total:.2f} USD\n"
        f"⏳ *Status:* PENDING PAYMENT"
    )
    kb = {
        'inline_keyboard': [
            [{'text': '📤 Upload & Deliver File', 'callback_data': f'adm_order_deliver:{order.id}'}],
            [{'text': '✅ Mark Paid', 'callback_data': f'adm_order_paid:{order.id}'}],
            [{'text': '❌ Cancel Request', 'callback_data': f'adm_order_cancel:{order.id}'}]
        ]
    }
    notify_admins(text, reply_markup=kb)

@router.message(SupportState.waiting_for_message)
async def process_support_message(message: Message, state: FSMContext):
    content = message.text.strip()
    if not content:
        await message.answer("Please type a valid support message.")
        return

    def create_ticket():
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )
        ticket = SupportTicket.objects.create(
            customer=profile,
            subject=content[:50] + ("..." if len(content) > 50 else "")
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=profile,
            is_admin_reply=False,
            message=content
        )
        return ticket

    ticket = await sync_to_async(create_ticket)()
    await state.clear()
    await sync_to_async(notify_ticket_created)(ticket, content)

    await message.answer(
        f"✅ *SUPPORT TICKET CREATED*\n\n"
        f"📋 *Ticket Number:* `{ticket.ticket_number}`\n"
        f"📝 *Message:* _{content}_\n"
        f"⏳ *Status:* OPEN\n\n"
        f"An admin has been notified and will reply directly to your chat shortly.",
        parse_mode="Markdown"
    )

@router.message(F.text.startswith("/ticket"))
async def create_ticket_cmd(message: Message, state: FSMContext):
    content = message.text.replace("/ticket", "").strip()
    if not content:
        await state.set_state(SupportState.waiting_for_message)
        await message.answer("Please type your ticket message below:")
        return

    def do_ticket():
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )
        ticket = SupportTicket.objects.create(
            customer=profile,
            subject=content[:50] + ("..." if len(content) > 50 else "")
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=profile,
            is_admin_reply=False,
            message=content
        )
        return ticket

    ticket = await sync_to_async(do_ticket)()
    await state.clear()
    await sync_to_async(notify_ticket_created)(ticket, content)

    await message.answer(
        f"✅ *SUPPORT TICKET CREATED*\n\n"
        f"📋 *Ticket Number:* `{ticket.ticket_number}`\n"
        f"Status: OPEN\n"
        f"An admin will review your message and reply shortly.",
        parse_mode="Markdown"
    )

@router.message(CustomRequestState.waiting_for_details)
async def process_custom_request_details(message: Message, state: FSMContext):
    req_notes = message.text.strip()
    if not req_notes:
        await message.answer("Please type your custom request details.")
        return

    def create_custom_order_and_ticket():
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )
        order = Order.objects.create(
            customer=profile,
            subtotal=0.00,
            discount=0.00,
            total=0.00,
            currency='USD',
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PENDING,
            custom_notes=req_notes
        )
        ticket = SupportTicket.objects.create(
            customer=profile,
            subject=f"Custom Order #{order.order_number}: {req_notes[:40]}"
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=profile,
            is_admin_reply=False,
            message=f"Custom Order Request #{order.order_number}:\n{req_notes}"
        )
        return profile, order

    profile, order = await sync_to_async(create_custom_order_and_ticket)()
    await state.clear()
    await sync_to_async(notify_custom_order_created)(order, req_notes)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    text = (
        f"✅ *CUSTOM DOCUMENT REQUEST SUBMITTED!*\n\n"
        f"📋 *Reference Number:* `{order.order_number}`\n"
        f"📝 *Specifications:* _{req_notes}_\n"
        f"⏳ *Status:* UNDER ADMIN REVIEW\n\n"
        f"Your custom template request has been logged. Our design team will review your specifications and send your completed file directly to your chat."
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=kb
    )

# CATCH-ALL HANDLER FOR UNRECOGNIZED TEXT MESSAGES
@router.message(F.text & ~F.text.startswith("/"))
async def handle_unrecognized_text(message: Message, state: FSMContext):
    # Check if text is a known reply keyboard command
    known_buttons = {
        "💰 TOP UP BALANCE", "👤 MY ACCOUNT", "📄 ID MOCKUPS", "📄 ID TEMPLATES",
        "🛂 PASSPORT MOCKUPS", "🛂 PASSPORT TEMPLATES", "🚗 DRIVER LICENSE MOCKUPS",
        "🚗 DRIVER LICENSE TEMPLATES", "🏢 BUSINESS DOCUMENTS", "🎓 CERTIFICATES",
        "📚 OTHER TEMPLATES", "🔎 VERIFICATION SERVICES", "🛒 MY ORDERS",
        "🎟 COUPONS", "💬 SUPPORT", "🔍 SEARCH", "🔐 ADMIN CONTROL", "🔐 ADMIN PANEL"
    }
    if message.text in known_buttons:
        return

    content = message.text.strip()
    
    def auto_create_ticket():
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )
        ticket = SupportTicket.objects.create(
            customer=profile,
            subject=content[:50] + ("..." if len(content) > 50 else "")
        )
        SupportMessage.objects.create(
            ticket=ticket,
            sender=profile,
            is_admin_reply=False,
            message=content
        )
        return ticket

    ticket = await sync_to_async(auto_create_ticket)()
    await sync_to_async(notify_ticket_created)(ticket, content)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Custom Document Request", callback_data="custom_req_prompt")],
        [InlineKeyboardButton(text="💬 Add More Details", callback_data="ticket_prompt")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])


    await message.answer(
        f"📩 *MESSAGE RECEIVED & LOGGED*\n\n"
        f"Thank you! Your message has been logged as Support Ticket `{ticket.ticket_number}`.\n\n"
        f"📝 *Message:* _{content}_\n\n"
        f"An admin will review your inquiry and reply directly to your Telegram chat shortly.\n\n"
        f"Need a custom document design or specific template? Choose an option below:",
        parse_mode="Markdown",
        reply_markup=kb
    )
