from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from accounts.services import get_or_create_telegram_user
from catalog.models import Product
from orders.models import Order, PaymentStatus, OrderStatus
from orders.services import create_order_from_product
from payments.services import initialize_order_payment, process_payment_confirmation
from telegram_bot.keyboards.inline import get_payment_methods_keyboard, get_product_detail_keyboard

router = Router()

from aiogram.fsm.context import FSMContext
from telegram_bot.states import CustomRequestState

@router.callback_query(F.data == "custom_req_prompt")
async def cb_custom_req_prompt(call: CallbackQuery, state: FSMContext):
    await state.set_state(CustomRequestState.waiting_for_details)
    text = (
        "📝 *CUSTOM DOCUMENT / VERIFICATION REQUEST*\n\n"
        "Can't find the exact template or verification service listed in our catalog?\n\n"
        "✍️ *Please type your detailed requirements directly below in this chat:*\n\n"
        "_Example: I need a custom business lease template for Florida state with custom logo placement._"
    )
    await call.message.edit_text(text, parse_mode="Markdown")
    await call.answer()


@router.message(F.text.startswith("/custom"))
async def handle_custom_request_cmd(message: Message):
    req_notes = message.text.replace("/custom", "").strip()
    if not req_notes:
        await message.answer("Please describe your custom request. Example:\n`/custom Need a custom certificate layout`", parse_mode="Markdown")
        return

    def create_custom_order():
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
        return profile, order

    profile, order = await sync_to_async(create_custom_order)()

    from notifications.services import notify_admins
    def alert_admins():
        cust = profile.first_name or profile.username or f"ID:{profile.telegram_user_id}"
        text = (
            f"🚨 *NEW CUSTOM ORDER REQUEST #{order.order_number}*\n\n"
            f"👤 *Customer:* `{cust}` (@{profile.username or 'N/A'})\n"
            f"📝 *Requirements:* _{req_notes}_\n"
            f"⏳ *Status:* UNDER ADMIN REVIEW"
        )
        kb = {
            'inline_keyboard': [
                [{'text': '📤 Upload & Deliver File', 'callback_data': f'adm_order_deliver:{order.id}'}],
                [{'text': '✅ Mark Paid', 'callback_data': f'adm_order_paid:{order.id}'}],
                [{'text': '❌ Cancel Request', 'callback_data': f'adm_order_cancel:{order.id}'}]
            ]
        }
        notify_admins(text, reply_markup=kb)

    await sync_to_async(alert_admins)()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    text = (
        f"✅ *CUSTOM DOCUMENT REQUEST SUBMITTED!*\n\n"
        f"📋 *Reference Number:* `{order.order_number}`\n"
        f"📝 *Specifications:* _{req_notes}_\n"
        f"⏳ *Status:* UNDER ADMIN REVIEW\n\n"
        f"Thank you! Your custom specifications have been logged. An admin will prepare your document and reply directly to your chat."
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=kb
    )

from notifications.services import notify_admins

def notify_new_order_placed(order):
    cust = order.customer.first_name or order.customer.username or f"ID:{order.customer.telegram_user_id}"
    items_str = ", ".join([item.product.name for item in order.items.all()]) or "Document Order"
    text = (
        f"🚨 *NEW ORDER CREATED #{order.order_number}*\n\n"
        f"👤 *Customer:* `{cust}` (@{order.customer.username or 'N/A'})\n"
        f"📦 *Item:* {items_str}\n"
        f"💰 *Total:* ${order.total:.2f} USD\n"
        f"💳 *Status:* {order.payment_status}"
    )
    kb = {
        'inline_keyboard': [
            [{'text': '📤 Upload & Deliver File', 'callback_data': f'adm_order_deliver:{order.id}'}],
            [{'text': '✅ Mark Paid', 'callback_data': f'adm_order_paid:{order.id}'}],
            [{'text': '❌ Cancel Order', 'callback_data': f'adm_order_cancel:{order.id}'}]
        ]
    }
    notify_admins(text, reply_markup=kb)

@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_now(call: CallbackQuery):
    prod_id = int(call.data.split(":")[1])

    def do_buy():
        product = Product.objects.filter(id=prod_id).first()
        if not product:
            return None, None
        profile = get_or_create_telegram_user(
            telegram_id=call.from_user.id,
            username=call.from_user.username or '',
            first_name=call.from_user.first_name or ''
        )
        order = create_order_from_product(customer=profile, product=product)
        return product, order

    product, order = await sync_to_async(do_buy)()
    if not product:
        await call.answer("Product not found.", show_alert=True)
        return

    await sync_to_async(notify_new_order_placed)(order)

    text = (
        f"🛒 *ORDER CREATED*\n\n"
        f"📋 *Order Number:* `{order.order_number}`\n"
        f"📦 *Item:* {product.name}\n"
        f"💰 *Total:* `${order.total}` {order.currency}\n"
        f"⏳ *Status:* PENDING PAYMENT\n\n"
        f"Please select your preferred payment method below:"
    )

    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_payment_methods_keyboard(order.order_number)
    )
    await call.answer()

@router.callback_query(F.data.startswith("pay:"))
async def cb_process_payment(call: CallbackQuery):
    parts = call.data.split(":")
    order_number = parts[1]
    provider_type = parts[2]

    def do_pay():
        order = Order.objects.filter(order_number=order_number).first()
        if not order:
            return None, None
        res = initialize_order_payment(order, provider_type)
        return order, res

    order, res = await sync_to_async(do_pay)()
    if not order:
        await call.answer("Order not found.", show_alert=True)
        return

    if provider_type == 'WALLET':
        from payments.services import process_wallet_payment
        res = await sync_to_async(process_wallet_payment)(order)
        if res.get('success'):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
            ])
            text = (
                f"✅ *PAYMENT CONFIRMED (PAID VIA WALLET)*\n\n"
                f"📋 *Order Number:* `{order.order_number}`\n"
                f"💰 *Amount Paid:* `${order.total}` {order.currency}\n"
                f"👛 *Available Balance:* `${res.get('remaining_balance')}`\n"
                f"⏳ *Status:* PAID / PROCESSING\n\n"
                f"Your payment has been received! Our admin team has been notified and is preparing your document. Your file will be delivered directly to your Telegram chat shortly!"
            )
            await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
            await call.answer("Order paid from wallet balance!", show_alert=True)
            return
        else:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 TOP UP BALANCE NOW", callback_data="topup_start")],
                [InlineKeyboardButton(text="⚡ PAY WITH CRYPTO", callback_data=f"pay:{order_number}:CRYPTO")],
                [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")]
            ])
            text = (
                f"❌ *INSUFFICIENT WALLET BALANCE*\n\n"
                f"📋 *Order:* `{order.order_number}`\n"
                f"💰 *Required Amount:* `${res.get('required')}` USD\n"
                f"👛 *Your Available Balance:* `${res.get('available')}` USD\n"
                f"⚠️ *Shortfall:* `${res.get('shortfall')}` USD\n\n"
                f"You do not have enough funds in your account balance to complete this order.\n"
                f"Please top up your balance or select another option below:"
            )
            await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
            await call.answer("Insufficient wallet balance!", show_alert=True)
            return

    if provider_type == 'MOCK':
        confirmed = await sync_to_async(process_payment_confirmation)(order_number)
        if confirmed:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
            ])
            text = (
                f"✅ *PAYMENT SUCCESSFUL*\n\n"
                f"📋 *Order Number:* `{order.order_number}`\n"
                f"💰 *Total:* `${order.total}` {order.currency}\n"
                f"⏳ *Status:* PAID / PROCESSING\n\n"
                f"Your payment has been verified! An admin has been notified and is preparing your document. Your file will be sent directly to this chat shortly!"
            )
            await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
            await call.answer("Payment verified!", show_alert=True)
            return


    instructions = res.get('instructions', 'Please complete your payment using the link below.')
    url = res.get('checkout_url', '')

    text = (
        f"💳 *PAYMENT INITIATED*\n\n"
        f"📋 *Order:* `{order.order_number}`\n"
        f"💰 *Amount:* `${order.total}` {order.currency}\n"
        f"Method: *{provider_type}*\n\n"
        f"ℹ️ {instructions}\n"
        f"{'🔗 Payment Link: ' + url if url else ''}"
    )

    await call.message.edit_text(text, parse_mode="Markdown")
    await call.answer()

@router.message(F.text == "🛒 MY ORDERS")
async def show_my_orders(message: Message):
    def fetch_orders():
        profile = get_or_create_telegram_user(telegram_id=message.from_user.id)
        orders = list(Order.objects.filter(customer=profile).order_by('-created_at')[:5])
        result = []
        for o in orders:
            t = o.download_tokens.first()
            result.append((o, t))
        return result

    order_tuples = await sync_to_async(fetch_orders)()

    if not order_tuples:
        await message.answer("🛒 You have no previous orders.")
        return

    msg = "🛒 *YOUR RECENT ORDERS:*\n\n"
    for o, token_obj in order_tuples:
        dl_link = f" (📥 Token: `{token_obj.token[:8]}...`)" if token_obj else ""
        notes = f"\n  Req: _{o.custom_notes[:30]}..._" if o.custom_notes else ""
        msg += (
            f"• *Order:* `{o.order_number}`\n"
            f"  Status: `{o.payment_status}` | Total: `${o.total}`{notes}\n"
            f"  Date: {o.created_at.strftime('%Y-%m-%d')}{dl_link}\n\n"
        )

    await message.answer(msg, parse_mode="Markdown")
