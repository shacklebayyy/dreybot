from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard(is_admin: bool = False):
    keyboard = [
        [KeyboardButton(text="🔎 VERIFICATION SERVICES")],
        [KeyboardButton(text="💰 TOP UP BALANCE"), KeyboardButton(text="👤 MY ACCOUNT")],
        [KeyboardButton(text="📄 ID TEMPLATES"), KeyboardButton(text="🛂 PASSPORT TEMPLATES")],
        [KeyboardButton(text="🚗 DRIVER LICENSE TEMPLATES"), KeyboardButton(text="🏢 BUSINESS DOCUMENTS")],
        [KeyboardButton(text="🎓 CERTIFICATES"), KeyboardButton(text="📚 OTHER TEMPLATES")],
        [KeyboardButton(text="🛒 MY ORDERS"), KeyboardButton(text="💬 SUPPORT")],
        [KeyboardButton(text="🎟 COUPONS"), KeyboardButton(text="🔍 SEARCH")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🔐 ADMIN CONTROL")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
