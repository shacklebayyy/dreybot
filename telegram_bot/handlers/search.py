from aiogram import Router, F
from aiogram.types import Message
from asgiref.sync import sync_to_async
from catalog.models import Product
from telegram_bot.keyboards.inline import get_products_keyboard

router = Router()

@router.message(F.text == "🔍 SEARCH")
async def ask_search(message: Message):
    await message.answer(
        "🔍 *SEARCH CATALOG*\n\n"
        "Send your search term using `/search <query>`.\n"
        "Example: `/search California` or `/search Passport`",
        parse_mode="Markdown"
    )

@router.message(F.text.startswith("/search"))
async def process_search(message: Message):
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.answer("Please specify a search term. Example: `/search California`", parse_mode="Markdown")
        return

    products = await sync_to_async(lambda: list(Product.objects.filter(name__icontains=query, is_active=True)[:10]))()

    if not products:
        await message.answer(f"🔍 No educational templates found matching *'{query}'*.", parse_mode="Markdown")
        return

    await message.answer(
        f"🔍 *SEARCH RESULTS FOR '{query}':*",
        parse_mode="Markdown",
        reply_markup=get_products_keyboard(products)
    )
