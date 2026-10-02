from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_countries_keyboard(countries, category_slug):
    buttons = []
    row = []
    for c in countries:
        btn = InlineKeyboardButton(
            text=f"{c.flag_emoji} {c.name}".strip(),
            callback_data=f"cat:{category_slug}:cnt:{c.iso_code}"
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="➕ NOT LISTED? ORDER ANY CUSTOM DOC", callback_data="custom_req_prompt")])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_us_states_keyboard(states):
    buttons = []
    row = []
    for s in states:
        btn = InlineKeyboardButton(
            text=s.name,
            callback_data=f"dl_state:{s.code}"
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="➕ NOT LISTED? ORDER ANY CUSTOM DOC", callback_data="custom_req_prompt")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="cat:driver-license-templates:cnt:US")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_products_keyboard(products):
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"{p.name} - ${p.price}",
            callback_data=f"prod:{p.id}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ OTHER / NOT LISTED (Custom Request)", callback_data="custom_req_prompt")])
    buttons.append([InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_detail_keyboard(product_id):
    buttons = [
        [InlineKeyboardButton(text="🛒 BUY NOW", callback_data=f"buy:{product_id}")],
        [InlineKeyboardButton(text="🛒 ADD TO CART", callback_data=f"add_cart:{product_id}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_methods_keyboard(order_number):
    buttons = [
        [InlineKeyboardButton(text="👛 PAY WITH WALLET BALANCE", callback_data=f"pay:{order_number}:WALLET")],
        [InlineKeyboardButton(text="⚡ PAY WITH CRYPTO (USDT / BTC / ETH)", callback_data=f"pay:{order_number}:CRYPTO")],
        [InlineKeyboardButton(text="💳 STRIPE / CARD PAYMENT", callback_data=f"pay:{order_number}:STRIPE")],
        [InlineKeyboardButton(text="🧪 TEST INSTANT CONFIRM", callback_data=f"pay:{order_number}:MOCK")],
        [InlineKeyboardButton(text="❌ CANCEL ORDER", callback_data=f"cancel_order:{order_number}")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_verification_services_keyboard(services):
    buttons = []
    for s in services:
        buttons.append([InlineKeyboardButton(
            text=f"{s.name} (${s.price})",
            callback_data=f"v_svc:{s.code}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ OTHER / NOT LISTED (Custom Request)", callback_data="custom_req_prompt")])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_consent_keyboard(service_code):
    buttons = [
        [InlineKeyboardButton(text="✅ I AGREE", callback_data=f"v_consent_yes:{service_code}")],
        [InlineKeyboardButton(text="❌ CANCEL", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_crypto_currency_keyboard(context="topup"):
    buttons = [
        [InlineKeyboardButton(text="₿ BTC", callback_data=f"crypto_curr:BTC:{context}"), InlineKeyboardButton(text="Ł LTC", callback_data=f"crypto_curr:LTC:{context}")],
        [InlineKeyboardButton(text="💎 TRX", callback_data=f"crypto_curr:TRX:{context}"), InlineKeyboardButton(text="Ξ ETH", callback_data=f"crypto_curr:ETH:{context}")],
        [InlineKeyboardButton(text="💵 USDT (TRC20 / ERC20)", callback_data=f"crypto_curr:USDT:{context}")],
        [InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_topup_amount_keyboard(currency):
    buttons = [
        [InlineKeyboardButton(text="$10", callback_data=f"topup_amt:10:{currency}"), InlineKeyboardButton(text="$25", callback_data=f"topup_amt:25:{currency}")],
        [InlineKeyboardButton(text="$50 (+ $5 Bonus)", callback_data=f"topup_amt:50:{currency}"), InlineKeyboardButton(text="$100 (+ $5 Bonus)", callback_data=f"topup_amt:100:{currency}")],
        [InlineKeyboardButton(text="✍️ ENTER CUSTOM AMOUNT (Min $7)", callback_data=f"topup_custom_prompt:{currency}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="topup_start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


