from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from accounts.services import get_or_create_telegram_user
from orders.models import Order
from payments.models import TopUpRequest, TopUpStatus
from telegram_bot.states import TopUpState
from telegram_bot.keyboards.inline import get_crypto_currency_keyboard, get_topup_amount_keyboard

router = Router()

@router.message(F.text == "👤 MY ACCOUNT")
async def show_account(message: Message):
    def fetch_account():
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )
        orders_count = Order.objects.filter(customer=profile).count()
        paid_orders = Order.objects.filter(customer=profile, payment_status='PAID').count()
        return profile, orders_count, paid_orders

    profile, orders_count, paid_orders = await sync_to_async(fetch_account)()

    text = (
        f"👤 *USER ACCOUNT OVERVIEW*\n"
        f"├ User ID: `{profile.telegram_user_id}`\n"
        f"├ Username: `@{profile.username or 'N/A'}`\n"
        f"├ 👛 *Total Available Balance:* `${profile.total_available_balance:.2f} USD`\n"
        f"├ 💵 Main Wallet Balance: `${profile.balance:.2f} USD`\n"
        f"├ 🎁 Active Bonus Balance: `${profile.bonus_balance:.2f} USD`\n"
        f"└ Register Date: `{profile.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
        f"💰 *BONUS PROGRAM*\n"
        f"└ Earn $5 bonus for deposits ≥$50!\n\n"
        f"📊 *ORDER STATS*\n"
        f"└ Total Orders: {orders_count} ({paid_orders} Completed)"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "💰 TOP UP BALANCE")
@router.callback_query(F.data == "topup_start")
async def topup_start_handler(event: Message | CallbackQuery):
    text = (
        "💳 *SELECT CRYPTO CURRENCY FOR TOP UP*\n\n"
        "Choose your preferred cryptocurrency to add funds to your account balance:"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=get_crypto_currency_keyboard("topup"))
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=get_crypto_currency_keyboard("topup"))

@router.callback_query(F.data.startswith("crypto_curr:"))
async def crypto_curr_selected(call: CallbackQuery):
    parts = call.data.split(":")
    currency = parts[1]
    context = parts[2]

    if context == "topup":
        def fetch_topup_rules():
            from core.models import SystemSetting
            min_amt = SystemSetting.get_setting('min_topup_amount', '7.00')
            bonus_thresh = SystemSetting.get_setting('topup_bonus_threshold', '50.00')
            bonus_amt = SystemSetting.get_setting('topup_bonus_amount', '5.00')
            return min_amt, bonus_thresh, bonus_amt

        min_amt, bonus_thresh, bonus_amt = await sync_to_async(fetch_topup_rules)()

        text = (
            f"💰 *SELECT DEPOSIT AMOUNT ({currency})*\n\n"
            f"📌 *Minimum Top Up:* `${min_amt} USD`\n"
            f"🎁 *Reward Bonus:* Earn `${bonus_amt} USD` bonus on deposits of `${bonus_thresh} USD` or more!\n\n"
            f"Select a preset amount below or click *[✍️ ENTER CUSTOM AMOUNT]* to type any custom deposit amount (e.g. $11, $15, $7):"
        )
        await call.message.edit_text(text, parse_mode="Markdown", reply_markup=get_topup_amount_keyboard(currency))
    else:
        await call.message.edit_text(f"Selected {currency} for checkout.", parse_mode="Markdown")
    await call.answer()

@router.callback_query(F.data.startswith("topup_custom_prompt:"))
async def cb_topup_custom_prompt(call: CallbackQuery, state: FSMContext):
    currency = call.data.split(":")[1]

    def get_min():
        from core.models import SystemSetting
        return SystemSetting.get_setting('min_topup_amount', '7.00')

    min_amt = await sync_to_async(get_min)()
    await state.update_data(topup_currency=currency)
    await state.set_state(TopUpState.waiting_for_custom_amount)

    await call.message.answer(
        f"✍️ *ENTER CUSTOM DEPOSIT AMOUNT*\n\n"
        f"🪙 *Selected Currency:* `{currency}`\n"
        f"📌 *Minimum Deposit:* `${min_amt} USD`\n\n"
        f"Please reply directly to this chat with your desired deposit amount (number only):\n"
        f"_Example: 11_",
        parse_mode="Markdown"
    )
    await call.answer()

@router.message(TopUpState.waiting_for_custom_amount)
async def process_custom_topup_amount(message: Message, state: FSMContext):
    raw_text = message.text.strip().replace("$", "")
    try:
        val = float(raw_text)
    except ValueError:
        await message.answer("⚠️ Please enter a valid number for your deposit amount (e.g. 11, 15, 25).")
        return

    def get_min():
        from core.models import SystemSetting
        return float(SystemSetting.get_setting('min_topup_amount', '7.00'))

    min_val = await sync_to_async(get_min)()
    if val < min_val:
        await message.answer(
            f"⚠️ *MINIMUM DEPOSIT IS ${min_val:.2f} USD*\n\n"
            f"You entered `${val:.2f} USD`. Please enter an amount of `${min_val:.2f} USD` or higher (e.g. 11, 15, 20):",
            parse_mode="Markdown"
        )
        return

    data = await state.get_data()
    currency = data.get("topup_currency", "USDT")
    amount_str = f"{val:.2f}"

    await state.clear()

    def fetch_crypto_details():
        import os
        from core.models import SystemSetting
        addr_key = f"{currency.lower()}_address"
        net_key = f"{currency.lower()}_network"

        defaults = {
            'BTC': ('bc1q0h7ql9m8zr3dk3f2f4vvjrgmz4kdt8v3daw2xm0pjr24efgde4ksh4skq6', 'Bitcoin Mainnet'),
            'LTC': ('ltc1qydca6ls4qs7wu7rhnm7fh9gpzfz200t5ecukfkqts26ulaelh29sm3pc04', 'Litecoin Mainnet'),
            'TRX': ('TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7', 'TRON (TRC20)'),
            'ETH': ('0x3d33a1641a61af1b3b499a1f6a236176bd1820b4', 'Ethereum (ERC20)'),
            'USDT': ('TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7', 'TRC20 / ERC20')
        }
        def_addr, def_net = defaults.get(currency.upper(), ('TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7', 'TRC20 / ERC20'))

        env_addr = os.getenv(f"CRYPTO_{currency.upper()}_ADDRESS", '')
        env_net = os.getenv(f"CRYPTO_{currency.upper()}_NETWORK", '')

        addr = env_addr or SystemSetting.get_setting(addr_key, def_addr)
        net = env_net or SystemSetting.get_setting(net_key, def_net)
        return addr, net

    addr, net = await sync_to_async(fetch_crypto_details)()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 SUBMIT PAYMENT PROOF / TX HASH", callback_data=f"topup_proof_prompt:{amount_str}:{currency}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="topup_start")]
    ])

    text = (
        f"⚡ *DEPOSIT INSTRUCTIONS ({currency})*\n\n"
        f"💰 *Custom Amount to Deposit:* `${amount_str} USD`\n"
        f"🪙 *Selected Coin:* `{currency}`\n"
        f"🌐 *Network:* `{net}`\n\n"
        f"Please send your deposit using the *{net}* to the receiving address below:\n"
        f"`{addr}`\n\n"
        f"After sending, click *[📤 SUBMIT PAYMENT PROOF]* below to submit your transaction hash or payment note for fast admin verification & balance crediting!"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data.startswith("topup_amt:"))
async def topup_amt_selected(call: CallbackQuery):
    parts = call.data.split(":")
    amount = parts[1]
    currency = parts[2]

    def fetch_crypto_details():
        import os
        from core.models import SystemSetting
        addr_key = f"{currency.lower()}_address"
        net_key = f"{currency.lower()}_network"

        defaults = {
            'BTC': ('bc1q0h7ql9m8zr3dk3f2f4vvjrgmz4kdt8v3daw2xm0pjr24efgde4ksh4skq6', 'Bitcoin Mainnet'),
            'LTC': ('ltc1qydca6ls4qs7wu7rhnm7fh9gpzfz200t5ecukfkqts26ulaelh29sm3pc04', 'Litecoin Mainnet'),
            'TRX': ('TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7', 'TRON (TRC20)'),
            'ETH': ('0x3d33a1641a61af1b3b499a1f6a236176bd1820b4', 'Ethereum (ERC20)'),
            'USDT': ('TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7', 'TRC20 / ERC20')
        }
        def_addr, def_net = defaults.get(currency.upper(), ('TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7', 'TRC20 / ERC20'))

        env_addr = os.getenv(f"CRYPTO_{currency.upper()}_ADDRESS", '')
        env_net = os.getenv(f"CRYPTO_{currency.upper()}_NETWORK", '')

        addr = env_addr or SystemSetting.get_setting(addr_key, def_addr)
        net = env_net or SystemSetting.get_setting(net_key, def_net)
        return addr, net

    addr, net = await sync_to_async(fetch_crypto_details)()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 SUBMIT PAYMENT PROOF / TX HASH", callback_data=f"topup_proof_prompt:{amount}:{currency}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="topup_start")]
    ])

    text = (
        f"⚡ *DEPOSIT INSTRUCTIONS ({currency})*\n\n"
        f"💰 *Amount to Deposit:* `${amount}.00 USD`\n"
        f"🪙 *Selected Coin:* `{currency}`\n"
        f"🌐 *Network:* `{net}`\n\n"
        f"Please send your deposit using the *{net}* to the receiving address below:\n"
        f"`{addr}`\n\n"
        f"After sending, click *[📤 SUBMIT PAYMENT PROOF]* below to submit your transaction hash or payment note for fast admin verification & balance crediting!"
    )
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("topup_proof_prompt:"))
async def cb_topup_proof_prompt(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    amount = parts[1]
    currency = parts[2]

    await state.update_data(topup_amount=amount, topup_currency=currency)
    await state.set_state(TopUpState.waiting_for_proof)

    await call.message.answer(
        f"📝 *SUBMIT TOP UP DEPOSIT PROOF*\n\n"
        f"Selected Amount: `${amount}.00 USD` ({currency})\n\n"
        f"Please reply directly to this chat with your *Transaction Hash (TxHash)*, screenshot link, or payment note:",
        parse_mode="Markdown"
    )
    await call.answer()

from notifications.services import notify_admins

def notify_topup_submitted(topup):
    cust = topup.customer.first_name or topup.customer.username or f"ID:{topup.customer.telegram_user_id}"
    tot_credit = topup.amount + topup.bonus_amount
    text = (
        f"🚨 *NEW TOP-UP PAYMENT PROOF #{topup.id}*\n\n"
        f"👤 *Customer:* `{cust}` (@{topup.customer.username or 'N/A'})\n"
        f"💵 *Deposit Amount:* ${topup.amount:.2f} USD\n"
        f"🎁 *Bonus Earned:* ${topup.bonus_amount:.2f} USD\n"
        f"💰 *Total Credit:* ${tot_credit:.2f} USD\n"
        f"🌐 *Method:* {topup.currency}\n"
        f"📄 *Proof/TxHash:* `{topup.tx_hash}`\n"
        f"⏳ *Status:* PENDING APPROVAL"
    )
    kb = {
        'inline_keyboard': [
            [{'text': f'✅ Approve & Credit ${tot_credit:.2f}', 'callback_data': f'adm_topup_app:{topup.id}'}],
            [{'text': '❌ Reject Deposit', 'callback_data': f'adm_topup_rej:{topup.id}'}]
        ]
    }
    notify_admins(text, reply_markup=kb)

@router.message(TopUpState.waiting_for_proof)
async def process_topup_proof(message: Message, state: FSMContext):
    proof_text = message.text.strip()
    data = await state.get_data()
    amount = data.get("topup_amount", "10")
    currency = data.get("topup_currency", "USDT")

    def create_topup():
        from core.models import SystemSetting
        profile = get_or_create_telegram_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or ''
        )

        thresh = float(SystemSetting.get_setting('topup_bonus_threshold', '50.00'))
        bonus_val = float(SystemSetting.get_setting('topup_bonus_amount', '5.00')) if float(amount) >= thresh else 0.00

        topup = TopUpRequest.objects.create(
            customer=profile,
            currency=currency,
            amount=amount,
            bonus_amount=bonus_val,
            tx_hash=proof_text[:250],
            status=TopUpStatus.PENDING
        )
        return profile, topup

    profile, topup = await sync_to_async(create_topup)()
    await state.clear()
    await sync_to_async(notify_topup_submitted)(topup)

    await message.answer(
        f"✅ *TOP UP REQUEST SUBMITTED!*\n\n"
        f"📋 *Reference:* `{topup.reference}`\n"
        f"🪙 *Currency:* `{topup.currency}`\n"
        f"💰 *Amount:* `${topup.amount}` USD"
        f"{' (+ $' + str(topup.bonus_amount) + ' Bonus Reward)' if topup.bonus_amount > 0 else ''}\n"
        f"📝 *Proof/TxHash:* `{topup.tx_hash}`\n"
        f"⏳ *Status:* PENDING ADMIN APPROVAL\n\n"
        f"An admin has been notified and will verify your transaction. Your account balance will be credited as soon as verified!",
        parse_mode="Markdown"
    )
