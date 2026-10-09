import os
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.db.models import Sum, Q

from accounts.models import UserProfile
from orders.models import Order, PaymentStatus, OrderStatus
from payments.models import TopUpRequest
from support.models import SupportTicket, SupportMessage
from verification.models import VerificationRequest, VerificationService
from telegram_bot.states import AdminState
from notifications.services import send_telegram_direct_message, send_telegram_document_file, notify_admins

router = Router()

def get_admin_profile(telegram_id: int):
    try:
        profile = UserProfile.objects.get(telegram_user_id=telegram_id)
        if profile.is_admin_role:
            return profile
    except UserProfile.DoesNotExist:
        pass

    from accounts.services import get_or_create_telegram_user
    profile = get_or_create_telegram_user(telegram_id=telegram_id)
    if profile and profile.is_admin_role:
        return profile
    return None

async def is_admin(telegram_id: int) -> bool:
    profile = await sync_to_async(get_admin_profile)(telegram_id)
    return profile is not None

# MAIN ADMIN DASHBOARD COMMAND
@router.message(F.text.in_({"/admin", "🔐 ADMIN CONTROL", "🔐 ADMIN PANEL"}))
async def admin_dashboard_cmd(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ Access denied. Admin permissions required.")
        return

    def get_stats_summary():
        pending_orders = Order.objects.filter(payment_status='PENDING').count()
        pending_topups = TopUpRequest.objects.filter(status='PENDING').count()
        open_tickets = SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
        pending_verifs = VerificationRequest.objects.filter(status__in=['AWAITING_PAYMENT', 'PROCESSING', 'QUEUED']).count()
        return pending_orders, pending_topups, open_tickets, pending_verifs

    p_orders, p_topups, o_tickets, p_verifs = await sync_to_async(get_stats_summary)()

    text = (
        "🔐 *ADMIN TELEGRAM MANAGEMENT DESK*\n\n"
        f"• Pending Custom & Product Orders: *{p_orders}*\n"
        f"• Pending Top-Up Deposit Proofs: *{p_topups}*\n"
        f"• Pending Verification Submissions: *{p_verifs}*\n"
        f"• Open Support Tickets: *{o_tickets}*\n\n"
        "Choose an action below to manage requests directly in Telegram:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛒 Manage Orders ({p_orders})", callback_data="adm_orders_menu")],
        [InlineKeyboardButton(text=f"💰 Top-Up Proofs ({p_topups})", callback_data="adm_topups_menu")],
        [InlineKeyboardButton(text=f"📋 Pending Verifications ({p_verifs})", callback_data="adm_verifications_menu")],
        [InlineKeyboardButton(text=f"🎫 Support Tickets ({o_tickets})", callback_data="adm_tickets_menu")],
        [InlineKeyboardButton(text="🔎 Verification Services ($1 BG Check)", callback_data="adm_services_menu")],
        [InlineKeyboardButton(text="📊 Revenue & Stats", callback_data="adm_stats_menu")],
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="adm_broadcast_prompt")]
    ])

    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

# ADMIN STATS MENU
@router.message(F.text == "/stats")
@router.callback_query(F.data == "adm_stats_menu")
async def admin_stats_cmd(event, state: FSMContext = None):
    telegram_id = event.from_user.id
    if not await is_admin(telegram_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        else:
            await event.answer("⛔ Access denied.")
        return

    def fetch_stats():
        tot_users = UserProfile.objects.count()
        tot_orders = Order.objects.count()
        paid_orders = Order.objects.filter(payment_status='PAID').count()
        revenue = Order.objects.filter(payment_status='PAID').aggregate(Sum('total'))['total__sum'] or 0.00
        tot_ver = VerificationRequest.objects.count()
        return tot_users, tot_orders, paid_orders, revenue, tot_ver

    tot_users, tot_orders, paid_orders, revenue, tot_ver = await sync_to_async(fetch_stats)()

    text = (
        "📊 *DREYDOCS REAL-TIME PLATFORM STATS*\n\n"
        f"• Total Customers: *{tot_users}*\n"
        f"• Total Orders: *{tot_orders}*\n"
        f"• Completed Paid Orders: *{paid_orders}*\n"
        f"• Total Platform Revenue: *${revenue:.2f} USD*\n"
        f"• Verification Requests: *{tot_ver}*"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back to Admin Desk", callback_data="adm_main_menu")]
    ])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=kb)

# RETURN TO ADMIN MENU
@router.callback_query(F.data == "adm_main_menu")
async def cb_adm_main_menu(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    def get_stats_summary():
        pending_orders = Order.objects.filter(payment_status='PENDING').count()
        pending_topups = TopUpRequest.objects.filter(status='PENDING').count()
        open_tickets = SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
        pending_verifs = VerificationRequest.objects.filter(status__in=['AWAITING_PAYMENT', 'PROCESSING', 'QUEUED']).count()
        return pending_orders, pending_topups, open_tickets, pending_verifs

    p_orders, p_topups, o_tickets, p_verifs = await sync_to_async(get_stats_summary)()

    text = (
        "🔐 *ADMIN TELEGRAM MANAGEMENT DESK*\n\n"
        f"• Pending Custom & Product Orders: *{p_orders}*\n"
        f"• Pending Top-Up Deposit Proofs: *{p_topups}*\n"
        f"• Pending Verification Submissions: *{p_verifs}*\n"
        f"• Open Support Tickets: *{o_tickets}*\n\n"
        "Choose an action below to manage requests directly in Telegram:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛒 Manage Orders ({p_orders})", callback_data="adm_orders_menu")],
        [InlineKeyboardButton(text=f"💰 Top-Up Proofs ({p_topups})", callback_data="adm_topups_menu")],
        [InlineKeyboardButton(text=f"📋 Pending Verifications ({p_verifs})", callback_data="adm_verifications_menu")],
        [InlineKeyboardButton(text=f"🎫 Support Tickets ({o_tickets})", callback_data="adm_tickets_menu")],
        [InlineKeyboardButton(text="🔎 Verification Services ($1 BG Check)", callback_data="adm_services_menu")],
        [InlineKeyboardButton(text="📊 Revenue & Stats", callback_data="adm_stats_menu")],
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="adm_broadcast_prompt")]
    ])

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

# ORDERS LIST & MANAGEMENT
@router.message(F.text == "/orders")
@router.callback_query(F.data == "adm_orders_menu")
async def admin_orders_list(event, state: FSMContext = None):
    telegram_id = event.from_user.id
    if not await is_admin(telegram_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        else:
            await event.answer("⛔ Access denied.")
        return

    def fetch_recent_orders():
        orders = list(Order.objects.select_related('customer').order_by('-created_at')[:8])
        results = []
        for o in orders:
            cust = o.customer.first_name or o.customer.username or f"ID:{o.customer.telegram_user_id}"
            results.append({
                'id': o.id,
                'order_number': o.order_number,
                'customer': cust,
                'cust_id': o.customer.telegram_user_id,
                'total': o.total,
                'payment_status': o.payment_status,
                'order_status': o.order_status,
                'custom_notes': o.custom_notes or ''
            })
        return results

    orders_data = await sync_to_async(fetch_recent_orders)()

    if not orders_data:
        msg = "🛒 *CUSTOMER ORDERS*\n\n❌ No available records found."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Admin Desk", callback_data="adm_main_menu")]])
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg, parse_mode="Markdown", reply_markup=kb)
            await event.answer()
        else:
            await event.answer(msg, parse_mode="Markdown", reply_markup=kb)
        return

    intro = "🛒 *RECENT ORDERS & CUSTOM REQUESTS*\nClick any order action button to approve payment, cancel, or dispatch document file:\n\n"
    if isinstance(event, CallbackQuery):
        await event.message.answer(intro, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(intro, parse_mode="Markdown")

    for o in orders_data:
        notes_str = f"\n📝 *Notes:* _{o['custom_notes']}_" if o['custom_notes'] else ""
        card = (
            f"📋 *Order #{o['order_number']}*\n"
            f"👤 Customer: `{o['customer']}`\n"
            f"💰 Amount: *${o['total']:.2f} USD*\n"
            f"💳 Pay Status: *{o['payment_status']}*\n"
            f"📦 Order Status: *{o['order_status']}*{notes_str}"
        )
        
        btns = []
        if o['payment_status'] == 'PENDING':
            btns.append(InlineKeyboardButton(text=f"💸 Deduct ${o['total']:.2f} Balance", callback_data=f"adm_order_deduct:{o['id']}"))
            btns.append(InlineKeyboardButton(text="✅ Mark Paid", callback_data=f"adm_order_paid:{o['id']}"))
        btns.append(InlineKeyboardButton(text="📤 Deliver File", callback_data=f"adm_order_deliver:{o['id']}"))
        if o['order_status'] != 'CANCELLED':
            btns.append(InlineKeyboardButton(text="❌ Cancel", callback_data=f"adm_order_cancel:{o['id']}"))

        kb = InlineKeyboardMarkup(inline_keyboard=[btns])
        
        if isinstance(event, CallbackQuery):
            await event.message.answer(card, parse_mode="Markdown", reply_markup=kb)
        else:
            await event.answer(card, parse_mode="Markdown", reply_markup=kb)

# DEDUCT BALANCE FOR ORDER
@router.callback_query(F.data.startswith("adm_order_deduct:"))
async def cb_adm_order_deduct(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    order_id = int(call.data.split(":")[1])

    def do_deduct():
        try:
            o = Order.objects.get(id=order_id)
            cust = o.customer
            cust.deduct_balance(o.total)
            o.payment_status = PaymentStatus.PAID
            o.order_status = OrderStatus.COMPLETED
            o.save()
            return o, cust.total_available_balance
        except Order.DoesNotExist:
            return None, None

    order, new_balance = await sync_to_async(do_deduct)()
    if not order:
        await call.answer("Order not found.", show_alert=True)
        return

    send_telegram_direct_message(
        order.customer.telegram_user_id,
        f"💸 *BALANCE DEDUCTED FOR ORDER #{order.order_number}*\n\n"
        f"💰 Deducted Amount: *${order.total:.2f} USD*\n"
        f"👛 Remaining Available Balance: *${new_balance:.2f} USD*\n\n"
        f"Status: *PAID & COMPLETED*"
    )

    await call.message.edit_text(
        f"💸 *DEDUCTED ${order.total:.2f} USD FROM CUSTOMER BALANCE FOR ORDER #{order.order_number}!*\n"
        f"Remaining Customer Balance: *${new_balance:.2f} USD*",
        parse_mode="Markdown"
    )
    await call.answer("Balance deducted & order marked paid!")

# MARK ORDER PAID
@router.callback_query(F.data.startswith("adm_order_paid:"))
async def cb_adm_order_paid(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    order_id = int(call.data.split(":")[1])

    def mark_paid():
        try:
            o = Order.objects.get(id=order_id)
            o.payment_status = PaymentStatus.PAID
            o.order_status = OrderStatus.COMPLETED
            o.save()
            return o
        except Order.DoesNotExist:
            return None

    order = await sync_to_async(mark_paid)()
    if not order:
        await call.answer("Order not found.", show_alert=True)
        return

    # Notify customer via Telegram
    send_telegram_direct_message(
        order.customer.telegram_user_id,
        f"✅ *PAYMENT CONFIRMED FOR ORDER #{order.order_number}!*\n\n"
        f"Your order of *${order.total:.2f} USD* has been marked PAID and COMPLETED by admin."
    )

    await call.message.edit_text(
        f"✅ *ORDER #{order.order_number} MARKED PAID & COMPLETED!*\nCustomer Telegram has been notified.",
        parse_mode="Markdown"
    )
    await call.answer("Order marked paid!")

# CANCEL ORDER
@router.callback_query(F.data.startswith("adm_order_cancel:"))
async def cb_adm_order_cancel(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    order_id = int(call.data.split(":")[1])

    def cancel_ord():
        try:
            o = Order.objects.get(id=order_id)
            o.order_status = OrderStatus.CANCELLED
            o.save()
            return o
        except Order.DoesNotExist:
            return None

    order = await sync_to_async(cancel_ord)()
    if not order:
        await call.answer("Order not found.", show_alert=True)
        return

    send_telegram_direct_message(
        order.customer.telegram_user_id,
        f"❌ *ORDER #{order.order_number} HAS BEEN CANCELLED.*\nIf you have questions, please submit a support ticket in chat."
    )

    await call.message.edit_text(
        f"❌ *ORDER #{order.order_number} CANCELLED.*",
        parse_mode="Markdown"
    )
    await call.answer("Order cancelled.")

# DELIVER FILE PROMPT FOR ORDER
@router.callback_query(F.data.startswith("adm_order_deliver:"))
async def cb_adm_order_deliver_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    order_id = int(call.data.split(":")[1])

    def get_ord():
        return Order.objects.filter(id=order_id).select_related('customer').first()

    order = await sync_to_async(get_ord)()
    if not order:
        await call.answer("Order not found.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_order_doc)
    await state.update_data(order_id=order.id)

    cust = order.customer.first_name or order.customer.username or f"ID:{order.customer.telegram_user_id}"

    await call.message.answer(
        f"📤 *UPLOAD DOCUMENT FOR ORDER #{order.order_number}*\n\n"
        f"👤 Customer: `{cust}` (Telegram ID: `{order.customer.telegram_user_id}`)\n\n"
        f"✍️ *Please attach a document file (PDF, ZIP, PSD, JPG, PNG) or type a download link directly below:*\n"
        f"It will be dispatched immediately into the customer's Telegram chat and mark the order PAID & COMPLETED.",
        parse_mode="Markdown"
    )
    await call.answer()

# PROCESS DELIVER FILE / LINK
@router.message(AdminState.waiting_for_order_doc)
async def process_adm_order_deliver_file(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        await message.answer("Error: Order context lost.")
        return

    def get_ord():
        return Order.objects.filter(id=order_id).select_related('customer').first()

    order = await sync_to_async(get_ord)()
    if not order:
        await state.clear()
        await message.answer("Order not found.")
        return

    customer_id = order.customer.telegram_user_id

    if message.document:
        bot = message.bot
        file_id = message.document.file_id
        file_name = message.document.file_name or f"document_{order.order_number}.pdf"
        file = await bot.get_file(file_id)
        
        # Dispatch document directly using Telegram bot sendDocument
        caption = f"📦 *YOUR COMPLETED DOCUMENT FILE (Order #{order.order_number})*\n\nThank you for choosing DreyDocs! Your document has been delivered by admin."
        try:
            await bot.send_document(chat_id=customer_id, document=file_id, caption=caption, parse_mode="Markdown")
            success = True
        except Exception as e:
            print(f"Failed sending doc file to user: {e}")
            success = False
    elif message.photo:
        bot = message.bot
        photo_id = message.photo[-1].file_id
        caption = f"📦 *YOUR COMPLETED DOCUMENT (Order #{order.order_number})*\n\nThank you for choosing DreyDocs! Your document file has been delivered by admin."
        try:
            await bot.send_photo(chat_id=customer_id, photo=photo_id, caption=caption, parse_mode="Markdown")
            success = True
        except Exception as e:
            print(f"Failed sending photo file to user: {e}")
            success = False
    else:
        # Plain text download link / notes
        doc_text = message.text.strip()
        msg_to_user = (
            f"📦 *DOCUMENT READY FOR ORDER #{order.order_number}*\n\n"
            f"Here is your completed document file / download link:\n"
            f"{doc_text}\n\n"
            f"Thank you for choosing DreyDocs!"
        )
        success = send_telegram_direct_message(customer_id, msg_to_user)

    if success:
        def finalize_order():
            order.payment_status = PaymentStatus.PAID
            order.order_status = OrderStatus.COMPLETED
            order.save()

        await sync_to_async(finalize_order)()
        await state.clear()
        await message.answer(
            f"✅ *DOCUMENT DISPATCHED & ORDER COMPLETED!*\n\n"
            f"Order `#{order.order_number}` has been delivered directly to customer Telegram chat `{customer_id}`.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ Failed to dispatch document to Telegram user ID {customer_id}. Please try again.")

# TOP-UPS LIST & MANAGEMENT
@router.message(F.text == "/topups")
@router.callback_query(F.data == "adm_topups_menu")
async def admin_topups_list(event, state: FSMContext = None):
    telegram_id = event.from_user.id
    if not await is_admin(telegram_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        else:
            await event.answer("⛔ Access denied.")
        return

    def fetch_pending_topups():
        topups = list(TopUpRequest.objects.filter(status='PENDING').select_related('customer').order_by('-created_at')[:10])
        results = []
        for t in topups:
            cust = t.customer.first_name or t.customer.username or f"ID:{t.customer.telegram_user_id}"
            b_amount = t.bonus_amount or Decimal('0.00')
            results.append({
                'id': t.id,
                'customer': cust,
                'cust_id': t.customer.telegram_user_id,
                'amount': t.amount,
                'bonus_amount': b_amount,
                'total_credit': t.amount + b_amount,
                'method': t.currency,
                'proof': t.tx_hash or t.notes or 'Submitted',
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return results

    topups_data = await sync_to_async(fetch_pending_topups)()

    if not topups_data:
        msg = "💰 *PENDING TOP-UP PROOFS*\n\n❌ No available records found."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Admin Desk", callback_data="adm_main_menu")]])
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg, parse_mode="Markdown", reply_markup=kb)
            await event.answer()
        else:
            await event.answer(msg, parse_mode="Markdown", reply_markup=kb)
        return

    intro = "💰 *PENDING TOP-UP DEPOSIT PROOFS*\nClick to approve & credit customer balance or reject:\n\n"
    if isinstance(event, CallbackQuery):
        await event.message.answer(intro, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(intro, parse_mode="Markdown")

    for t in topups_data:
        card = (
            f"💵 *Top-Up Request #{t['id']}*\n"
            f"👤 Customer: `{t['customer']}`\n"
            f"💰 Amount: *${t['amount']:.2f} USD* (Bonus: *${t['bonus_amount']:.2f}*)\n"
            f"💳 Total Credit: *${t['total_credit']:.2f} USD*\n"
            f"🌐 Method: `{t['method']}`\n"
            f"📄 Proof: _{t['proof']}_\n"
            f"📅 Submitted: {t['created_at']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"✅ Approve ${t['total_credit']:.2f}", callback_data=f"adm_topup_app:{t['id']}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_topup_rej:{t['id']}")
        ]])
        
        if isinstance(event, CallbackQuery):
            await event.message.answer(card, parse_mode="Markdown", reply_markup=kb)
        else:
            await event.answer(card, parse_mode="Markdown", reply_markup=kb)

# APPROVE TOPUP
@router.callback_query(F.data.startswith("adm_topup_app:"))
async def cb_adm_topup_app(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    topup_id = int(call.data.split(":")[1])

    def do_approve():
        try:
            t = TopUpRequest.objects.get(id=topup_id)
            if t.status != 'PENDING':
                return None, "Already processed"
            
            t.status = 'APPROVED'
            t.save()

            cust = t.customer
            cust.balance += t.amount
            cust.bonus_balance += t.bonus_amount
            cust.save()

            return t, None
        except TopUpRequest.DoesNotExist:
            return None, "TopUp not found"

    topup, err = await sync_to_async(do_approve)()
    if err or not topup:
        await call.answer(err or "Failed", show_alert=True)
        return

    total_credit = topup.amount + topup.bonus_amount
    send_telegram_direct_message(
        topup.customer.telegram_user_id,
        f"🎉 *DEPOSIT APPROVED & CREDITED!*\n\n"
        f"Your top-up deposit of *${topup.amount:.2f} USD* + *${topup.bonus_amount:.2f} Bonus* (${total_credit:.2f} Total) has been credited to your balance!\n\n"
        f"👛 *New Balance:* ${topup.customer.balance:.2f} USD | Bonus: ${topup.customer.bonus_balance:.2f}"
    )

    await call.message.edit_text(
        f"✅ *TOP-UP #{topup.id} APPROVED & CREDITED (${total_credit:.2f} USD)*\nCustomer notified in Telegram chat.",
        parse_mode="Markdown"
    )
    await call.answer("Deposit approved & credited!")

# REJECT TOPUP
@router.callback_query(F.data.startswith("adm_topup_rej:"))
async def cb_adm_topup_rej(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    topup_id = int(call.data.split(":")[1])

    def do_reject():
        try:
            t = TopUpRequest.objects.get(id=topup_id)
            t.status = 'REJECTED'
            t.save()
            return t
        except TopUpRequest.DoesNotExist:
            return None

    topup = await sync_to_async(do_reject)()
    if not topup:
        await call.answer("Topup not found", show_alert=True)
        return

    send_telegram_direct_message(
        topup.customer.telegram_user_id,
        f"❌ *TOP-UP PROOF UNVERIFIED*\n\n"
        f"Your deposit proof for top-up #{topup.id} could not be verified. Please double-check your TxHash/screenshot and resubmit proof, or contact support."
    )

    await call.message.edit_text(f"❌ *TOP-UP #{topup.id} REJECTED.*", parse_mode="Markdown")
    await call.answer("Deposit rejected.")

# SUPPORT TICKETS LIST & MANAGEMENT
@router.message(F.text == "/tickets")
@router.callback_query(F.data == "adm_tickets_menu")
async def admin_tickets_list(event, state: FSMContext = None):
    telegram_id = event.from_user.id
    if not await is_admin(telegram_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        else:
            await event.answer("⛔ Access denied.")
        return

    def fetch_open_tickets():
        tickets = list(SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).select_related('customer').order_by('-updated_at')[:8])
        results = []
        for t in tickets:
            cust = t.customer.first_name or t.customer.username or f"ID:{t.customer.telegram_user_id}"
            last_msg = t.messages.order_by('-created_at').first()
            msg_text = last_msg.message if last_msg else t.subject
            results.append({
                'id': t.id,
                'ticket_number': t.ticket_number,
                'customer': cust,
                'subject': t.subject,
                'status': t.status,
                'last_msg': msg_text
            })
        return results

    tickets_data = await sync_to_async(fetch_open_tickets)()

    if not tickets_data:
        msg = "🎫 *SUPPORT TICKETS*\n\n❌ No available records found."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Admin Desk", callback_data="adm_main_menu")]])
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg, parse_mode="Markdown", reply_markup=kb)
            await event.answer()
        else:
            await event.answer(msg, parse_mode="Markdown", reply_markup=kb)
        return

    intro = "🎫 *ACTIVE OPEN SUPPORT TICKETS*\nClick reply to write a response directly to the customer in Telegram:\n\n"
    if isinstance(event, CallbackQuery):
        await event.message.answer(intro, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(intro, parse_mode="Markdown")

    for t in tickets_data:
        card = (
            f"📋 *Ticket #{t['ticket_number']}*\n"
            f"👤 Customer: `{t['customer']}`\n"
            f"💬 Message: _{t['last_msg']}_\n"
            f"⏳ Status: *{t['status']}*"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="💬 Reply to Ticket", callback_data=f"adm_reply_tck:{t['id']}"),
            InlineKeyboardButton(text="✅ Close Ticket", callback_data=f"adm_close_tck:{t['id']}")
        ]])
        
        if isinstance(event, CallbackQuery):
            await event.message.answer(card, parse_mode="Markdown", reply_markup=kb)
        else:
            await event.answer(card, parse_mode="Markdown", reply_markup=kb)

# PROMPT REPLY TO TICKET
@router.callback_query(F.data.startswith("adm_reply_tck:"))
async def cb_adm_reply_tck_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    ticket_id = int(call.data.split(":")[1])

    def get_tck():
        return SupportTicket.objects.filter(id=ticket_id).select_related('customer').first()

    ticket = await sync_to_async(get_tck)()
    if not ticket:
        await call.answer("Ticket not found.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_ticket_reply)
    await state.update_data(ticket_id=ticket.id)

    cust = ticket.customer.first_name or ticket.customer.username or f"ID:{ticket.customer.telegram_user_id}"

    await call.message.answer(
        f"💬 *REPLY TO SUPPORT TICKET #{ticket.ticket_number}*\n\n"
        f"👤 Customer: `{cust}`\n"
        f"📋 Subject: _{ticket.subject}_\n\n"
        f"✍️ *Please type your reply message directly below:*\n"
        f"It will be sent immediately to the customer in their Telegram chat.",
        parse_mode="Markdown"
    )
    await call.answer()

# PROCESS TICKET REPLY TEXT
@router.message(AdminState.waiting_for_ticket_reply)
async def process_adm_ticket_reply(message: Message, state: FSMContext):
    reply_text = message.text.strip()
    if not reply_text:
        await message.answer("Please type a valid reply text.")
        return

    data = await state.get_data()
    ticket_id = data.get("ticket_id")

    def save_admin_reply():
        try:
            ticket = SupportTicket.objects.get(id=ticket_id)
            admin_profile = get_admin_profile(message.from_user.id)
            SupportMessage.objects.create(
                ticket=ticket,
                sender=admin_profile,
                is_admin_reply=True,
                message=reply_text
            )
            ticket.status = 'IN_PROGRESS'
            ticket.save()
            return ticket
        except SupportTicket.DoesNotExist:
            return None

    ticket = await sync_to_async(save_admin_reply)()
    if not ticket:
        await state.clear()
        await message.answer("Error: Support ticket not found.")
        return

    # Dispatch reply to customer chat
    customer_id = ticket.customer.telegram_user_id
    msg_to_customer = (
        f"💬 *SUPPORT DESK REPLY (Ticket #{ticket.ticket_number})*\n\n"
        f"{reply_text}\n\n"
        f"_✍️ You can type directly in this chat anytime to send a follow-up message to support._"
    )
    send_telegram_direct_message(customer_id, msg_to_customer)

    await state.clear()
    await message.answer(
        f"✅ *REPLY SENT TO CUSTOMER TELEGRAM CHAT!*\n\n"
        f"📋 Ticket `#{ticket.ticket_number}` updated to IN_PROGRESS.",
        parse_mode="Markdown"
    )

# CLOSE SUPPORT TICKET
@router.callback_query(F.data.startswith("adm_close_tck:"))
async def cb_adm_close_tck(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    ticket_id = int(call.data.split(":")[1])

    def close_tck():
        try:
            t = SupportTicket.objects.get(id=ticket_id)
            t.status = 'CLOSED'
            t.save()
            return t
        except SupportTicket.DoesNotExist:
            return None

    ticket = await sync_to_async(close_tck)()
    if not ticket:
        await call.answer("Ticket not found", show_alert=True)
        return

    send_telegram_direct_message(
        ticket.customer.telegram_user_id,
        f"🔒 *SUPPORT TICKET #{ticket.ticket_number} RESOLVED & CLOSED.*\nIf you need further assistance, simply type a new message in this chat."
    )

    await call.message.edit_text(f"✅ *TICKET #{ticket.ticket_number} CLOSED.*", parse_mode="Markdown")
    await call.answer("Ticket closed.")

# VERIFICATION SUBMISSIONS LIST & MANAGEMENT
@router.message(F.text == "/verifications")
@router.callback_query(F.data == "adm_verifications_menu")
async def admin_verifications_list(event, state: FSMContext = None):
    telegram_id = event.from_user.id
    if not await is_admin(telegram_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        else:
            await event.answer("⛔ Access denied.")
        return

    def fetch_pending_verifs():
        verifs = list(VerificationRequest.objects.filter(status__in=['AWAITING_PAYMENT', 'PROCESSING', 'QUEUED']).select_related('customer', 'service').order_by('-created_at')[:10])
        results = []
        for v in verifs:
            cust = v.customer.first_name or v.customer.username or f"ID:{v.customer.telegram_user_id}"
            data_str = v.result.get('submitted_data', 'No submitted data attached') if isinstance(v.result, dict) else str(v.result)
            results.append({
                'id': v.id,
                'verification_number': v.verification_number,
                'customer': cust,
                'service_name': v.service.name,
                'price': v.price,
                'currency': v.currency,
                'status': v.status,
                'data': data_str,
                'created_at': v.created_at.strftime('%Y-%m-%d %H:%M')
            })
        return results

    verifs_data = await sync_to_async(fetch_pending_verifs)()

    if not verifs_data:
        msg = "📋 *PENDING VERIFICATION REQUESTS*\n\n❌ No available records found."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Admin Desk", callback_data="adm_main_menu")]])
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg, parse_mode="Markdown", reply_markup=kb)
            await event.answer()
        else:
            await event.answer(msg, parse_mode="Markdown", reply_markup=kb)
        return

    intro = "📋 *PENDING VERIFICATION SUBMISSIONS*\nClick deliver to send verification results or mark failed:\n\n"
    if isinstance(event, CallbackQuery):
        await event.message.answer(intro, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(intro, parse_mode="Markdown")

    for v in verifs_data:
        card = (
            f"📋 *Verification #{v['verification_number']}*\n"
            f"👤 Customer: `{v['customer']}`\n"
            f"🔎 Service: *{v['service_name']}* (${v['price']:.2f} {v['currency']})\n"
            f"📄 Data:\n```\n{v['data']}\n```\n"
            f"⏳ Status: *{v['status']}*"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"💸 Deduct ${v['price']:.2f}", callback_data=f"adm_verif_deduct:{v['id']}"),
            InlineKeyboardButton(text="📤 Send Result", callback_data=f"adm_verif_deliver:{v['id']}"),
            InlineKeyboardButton(text="❌ Mark Failed", callback_data=f"adm_verif_fail:{v['id']}")
        ]])
        
        if isinstance(event, CallbackQuery):
            await event.message.answer(card, parse_mode="Markdown", reply_markup=kb)
        else:
            await event.answer(card, parse_mode="Markdown", reply_markup=kb)

# DEDUCT BALANCE FOR VERIFICATION REQUEST
@router.callback_query(F.data.startswith("adm_verif_deduct:"))
async def cb_adm_verif_deduct(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    verif_id = int(call.data.split(":")[1])

    from verification.models import VerificationRequestStatus
    from django.utils import timezone

    def do_deduct():
        try:
            r = VerificationRequest.objects.get(id=verif_id)
            cust = r.customer
            cust.deduct_balance(r.price)
            r.status = VerificationRequestStatus.COMPLETED
            r.completed_at = timezone.now()
            r.save()
            return r, cust.total_available_balance
        except VerificationRequest.DoesNotExist:
            return None, None

    req, new_balance = await sync_to_async(do_deduct)()
    if not req:
        await call.answer("Verification request not found.", show_alert=True)
        return

    send_telegram_direct_message(
        req.customer.telegram_user_id,
        f"💸 *BALANCE DEDUCTED FOR VERIFICATION #{req.verification_number}*\n\n"
        f"🔎 Service: *{req.service.name}*\n"
        f"💰 Deducted Amount: *${req.price:.2f} USD*\n"
        f"👛 Remaining Available Balance: *${new_balance:.2f} USD*\n\n"
        f"Status: *COMPLETED*"
    )

    await call.message.edit_text(
        f"💸 *DEDUCTED ${req.price:.2f} USD FROM CUSTOMER BALANCE FOR VERIFICATION #{req.verification_number}!*\n"
        f"Remaining Customer Balance: *${new_balance:.2f} USD*",
        parse_mode="Markdown"
    )
    await call.answer("Balance deducted & verification completed!")


# BROADCAST PROMPT & EXECUTION
@router.callback_query(F.data == "adm_broadcast_prompt")
async def cb_adm_broadcast_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_broadcast)
    await call.message.answer(
        "📢 *BROADCAST ANNOUNCEMENT*\n\n"
        "Please type the announcement message you wish to send to ALL registered Telegram bot users below:",
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(AdminState.waiting_for_broadcast)
@router.message(F.text.startswith("/broadcast"))
async def admin_broadcast_cmd(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ Access denied.")
        return

    if message.text.startswith("/broadcast"):
        broadcast_msg = message.text.replace("/broadcast", "").strip()
    else:
        broadcast_msg = message.text.strip()

    if not broadcast_msg:
        await message.answer("Usage: `/broadcast <your message here>`", parse_mode="Markdown")
        return

    def fetch_users():
        return list(UserProfile.objects.filter(is_blocked=False).values_list('telegram_user_id', flat=True))

    user_ids = await sync_to_async(fetch_users)()
    count = 0
    for tid in user_ids:
        if tid:
            success = send_telegram_direct_message(tid, f"📢 *ANNOUNCEMENT:*\n\n{broadcast_msg}")
            if success:
                count += 1

    await state.clear()
    await message.answer(f"✅ Broadcast sent successfully to {count} users.")

# VERIFICATION SERVICES MANAGEMENT CONTROL
@router.message(F.text == "/services")
@router.callback_query(F.data == "adm_services_menu")
async def admin_services_list(event, state: FSMContext = None):
    telegram_id = event.from_user.id
    if not await is_admin(telegram_id):
        if isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        else:
            await event.answer("⛔ Access denied.")
        return

    def fetch_services():
        svcs = list(VerificationService.objects.all().order_by('id'))
        results = []
        for s in svcs:
            results.append({
                'id': s.id,
                'name': s.name,
                'code': s.code,
                'price': s.price,
                'currency': s.currency,
                'active': s.active,
            })
        return results

    svcs_data = await sync_to_async(fetch_services)()

    if not svcs_data:
        msg = "🔎 *VERIFICATION SERVICES CONTROL*\n\nNo verification services found in database."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Admin Desk", callback_data="adm_main_menu")]])
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg, parse_mode="Markdown", reply_markup=kb)
            await event.answer()
        else:
            await event.answer(msg, parse_mode="Markdown", reply_markup=kb)
        return

    intro = "🔎 *VERIFICATION SERVICES CONTROL PANEL*\nManage prices and active status for all verification checks (including $1 Background Check):\n\n"
    if isinstance(event, CallbackQuery):
        await event.message.answer(intro, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(intro, parse_mode="Markdown")

    for s in svcs_data:
        status_str = "🟢 Active" if s['active'] else "🔴 Disabled"
        card = (
            f"📋 *{s['name']}*\n"
            f"🔑 Code: `{s['code']}`\n"
            f"💰 Price: *${s['price']:.2f} {s['currency']}*\n"
            f"⚡ Status: {status_str}"
        )
        toggle_btn_text = "🔴 Disable" if s['active'] else "🟢 Enable"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=toggle_btn_text, callback_data=f"adm_svc_toggle:{s['id']}"),
            InlineKeyboardButton(text="✏️ Edit Price", callback_data=f"adm_svc_price:{s['id']}")
        ]])

        if isinstance(event, CallbackQuery):
            await event.message.answer(card, parse_mode="Markdown", reply_markup=kb)
        else:
            await event.answer(card, parse_mode="Markdown", reply_markup=kb)

# TOGGLE VERIFICATION SERVICE ACTIVE STATUS
@router.callback_query(F.data.startswith("adm_svc_toggle:"))
async def cb_adm_svc_toggle(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    svc_id = int(call.data.split(":")[1])

    def toggle_svc():
        try:
            s = VerificationService.objects.get(id=svc_id)
            s.active = not s.active
            s.save()
            return s
        except VerificationService.DoesNotExist:
            return None

    svc = await sync_to_async(toggle_svc)()
    if not svc:
        await call.answer("Service not found", show_alert=True)
        return

    status_str = "🟢 Active" if svc.active else "🔴 Disabled"
    await call.message.edit_text(
        f"📋 *{svc.name}*\n"
        f"🔑 Code: `{svc.code}`\n"
        f"💰 Price: *${svc.price:.2f} {svc.currency}*\n"
        f"⚡ Status: {status_str}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔴 Disable" if svc.active else "🟢 Enable", callback_data=f"adm_svc_toggle:{svc.id}"),
            InlineKeyboardButton(text="✏️ Edit Price", callback_data=f"adm_svc_price:{svc.id}")
        ]])
    )
    await call.answer(f"Status updated to {'Active' if svc.active else 'Disabled'}")

# PROMPT EDIT PRICE FOR VERIFICATION SERVICE
@router.callback_query(F.data.startswith("adm_svc_price:"))
async def cb_adm_svc_price_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    svc_id = int(call.data.split(":")[1])

    def get_svc():
        return VerificationService.objects.filter(id=svc_id).first()

    svc = await sync_to_async(get_svc)()
    if not svc:
        await call.answer("Service not found.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_service_price)
    await state.update_data(svc_id=svc.id)

    await call.message.answer(
        f"✏️ *EDIT PRICE FOR SERVICE: {svc.name}*\n\n"
        f"Current Price: `${svc.price:.2f} {svc.currency}`\n\n"
        f"✍️ *Please enter the new price numeric value below (e.g. 1.00):*",
        parse_mode="Markdown"
    )
    await call.answer()

# PROCESS SERVICE NEW PRICE
@router.message(AdminState.waiting_for_service_price)
async def process_adm_svc_price(message: Message, state: FSMContext):
    text_val = message.text.strip().lstrip('$')
    try:
        new_price = Decimal(text_val)
        if new_price < 0:
            raise ValueError
    except Exception:
        await message.answer("❌ Invalid price format. Please enter a valid positive number like `1.00` or `5.00`:", parse_mode="Markdown")
        return

    data = await state.get_data()
    svc_id = data.get("svc_id")

    def update_price():
        try:
            s = VerificationService.objects.get(id=svc_id)
            s.price = new_price
            s.save()
            return s
        except VerificationService.DoesNotExist:
            return None

    svc = await sync_to_async(update_price)()
    await state.clear()

    if not svc:
        await message.answer("Error: Service not found.")
        return

    await message.answer(
        f"✅ *PRICE UPDATED FOR {svc.name}!*\n\n"
        f"New Price: *${svc.price:.2f} {svc.currency}*",
        parse_mode="Markdown"
    )

# PROMPT ADMIN TO SEND VERIFICATION RESULT
@router.callback_query(F.data.startswith("adm_verif_deliver:"))
async def cb_adm_verif_deliver_prompt(call: CallbackQuery, state: FSMContext):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    verif_id = int(call.data.split(":")[1])

    def get_req():
        return VerificationRequest.objects.filter(id=verif_id).select_related('customer', 'service').first()

    req = await sync_to_async(get_req)()
    if not req:
        await call.answer("Verification request not found.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_verif_result)
    await state.update_data(verif_id=req.id)

    cust = req.customer.first_name or req.customer.username or f"ID:{req.customer.telegram_user_id}"

    await call.message.answer(
        f"📤 *DELIVER VERIFICATION RESULT FOR REQUEST #{req.verification_number}*\n\n"
        f"👤 Customer: `{cust}` (Telegram ID: `{req.customer.telegram_user_id}`)\n"
        f"🔎 Service: *{req.service.name}*\n\n"
        f"✍️ *Please attach a document file (PDF/PNG) or type the verification result directly below:*\n"
        f"It will be sent immediately to the customer's Telegram chat and mark the verification request COMPLETED.",
        parse_mode="Markdown"
    )
    await call.answer()

# PROCESS ADMIN VERIFICATION RESULT DISPATCH
@router.message(AdminState.waiting_for_verif_result)
async def process_adm_verif_result(message: Message, state: FSMContext):
    data = await state.get_data()
    verif_id = data.get("verif_id")
    if not verif_id:
        await state.clear()
        await message.answer("Error: Verification context lost.")
        return

    def get_req():
        return VerificationRequest.objects.filter(id=verif_id).select_related('customer', 'service').first()

    req = await sync_to_async(get_req)()
    if not req:
        await state.clear()
        await message.answer("Verification request not found.")
        return

    customer_id = req.customer.telegram_user_id
    success = False

    if message.document:
        bot = message.bot
        file_id = message.document.file_id
        caption = f"📊 *VERIFICATION RESULT READY (#{req.verification_number})*\n\n🔎 Service: *{req.service.name}*\nThank you for using DreyDocs Verification Services!"
        try:
            await bot.send_document(chat_id=customer_id, document=file_id, caption=caption, parse_mode="Markdown")
            success = True
        except Exception as e:
            print(f"Failed sending verif doc to user: {e}")
            success = False
    elif message.photo:
        bot = message.bot
        photo_id = message.photo[-1].file_id
        caption = f"📊 *VERIFICATION RESULT READY (#{req.verification_number})*\n\n🔎 Service: *{req.service.name}*\nThank you for using DreyDocs Verification Services!"
        try:
            await bot.send_photo(chat_id=customer_id, photo=photo_id, caption=caption, parse_mode="Markdown")
            success = True
        except Exception as e:
            print(f"Failed sending verif photo to user: {e}")
            success = False
    else:
        res_text = message.text.strip()
        msg_to_user = (
            f"📊 *VERIFICATION RESULT FOR REQUEST #{req.verification_number}*\n\n"
            f"🔎 Service: *{req.service.name}*\n\n"
            f"📋 *RESULTS:*\n"
            f"{res_text}\n\n"
            f"Thank you for choosing DreyDocs!"
        )
        success = send_telegram_direct_message(customer_id, msg_to_user)

    if success:
        from verification.models import VerificationRequestStatus
        from django.utils import timezone

        def finalize_verif():
            req.status = VerificationRequestStatus.COMPLETED
            req.completed_at = timezone.now()
            req.save()

        await sync_to_async(finalize_verif)()
        await state.clear()
        await message.answer(
            f"✅ *VERIFICATION RESULT DISPATCHED!*\n\n"
            f"Request `#{req.verification_number}` has been delivered directly to customer Telegram chat `{customer_id}`.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(f"❌ Failed to dispatch result to Telegram user ID {customer_id}. Please try again.")

# MARK VERIFICATION FAILED
@router.callback_query(F.data.startswith("adm_verif_fail:"))
async def cb_adm_verif_fail(call: CallbackQuery):
    if not await is_admin(call.from_user.id):
        await call.answer("Access denied", show_alert=True)
        return

    verif_id = int(call.data.split(":")[1])

    from verification.models import VerificationRequestStatus

    def fail_verif():
        try:
            r = VerificationRequest.objects.get(id=verif_id)
            r.status = VerificationRequestStatus.FAILED
            r.failure_reason = "Verification check unverified or rejected by provider."
            r.save()
            return r
        except VerificationRequest.DoesNotExist:
            return None

    req = await sync_to_async(fail_verif)()
    if not req:
        await call.answer("Request not found", show_alert=True)
        return

    send_telegram_direct_message(
        req.customer.telegram_user_id,
        f"❌ *VERIFICATION REQUEST #{req.verification_number} UNVERIFIED / FAILED.*\nIf you have questions, please submit a support ticket in chat."
    )

    await call.message.edit_text(f"❌ *VERIFICATION #{req.verification_number} MARKED FAILED.*", parse_mode="Markdown")
    await call.answer("Marked failed.")


