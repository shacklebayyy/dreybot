from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from accounts.services import get_or_create_telegram_user
from telegram_bot.keyboards.reply import get_main_menu_keyboard

from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
@router.message(Command("menu"))
@router.message(F.text.in_({"MAIN MENU", "Menu", "MENU", "/menu"}))
async def cmd_start(message: Message):
    tg_user = message.from_user
    profile = await sync_to_async(get_or_create_telegram_user)(
        telegram_id=tg_user.id,
        username=tg_user.username or '',
        first_name=tg_user.first_name or '',
        last_name=tg_user.last_name or '',
        language_code=tg_user.language_code or 'en'
    )

    admin_role = profile.is_admin_role

    welcome_text = (
        f"Welcome to DreyDocs 👋\n\n"
        f"Learning Documents & Professional Design Templates\n\n"
        f"Browse educational document templates, purchase your files, and access authorized verification services.\n\n"
        f"👤 *User Profile:*\n"
        f"• Name: `{profile.full_name}`\n"
        f"• Telegram ID: `{profile.telegram_user_id}`"
    )
    if admin_role:
        welcome_text += "\n• Role: *Admin (Telegram Control Panel Active)*"

    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(is_admin=admin_role)
    )

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery):
    tg_user = call.from_user
    profile = await sync_to_async(get_or_create_telegram_user)(
        telegram_id=tg_user.id,
        username=tg_user.username or '',
        first_name=tg_user.first_name or ''
    )
    await call.message.answer(
        "Main Menu:",
        reply_markup=get_main_menu_keyboard(is_admin=profile.is_admin_role)
    )
    await call.answer()
