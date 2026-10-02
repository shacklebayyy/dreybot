from aiogram import Router, F
from aiogram.types import Message
from asgiref.sync import sync_to_async
from coupons.models import Coupon

router = Router()

@router.message(F.text == "🎟 COUPONS")
async def show_coupons(message: Message):
    coupons = await sync_to_async(lambda: list(Coupon.objects.filter(active=True)))()
    if not coupons:
        await message.answer("🎟 No active promotional coupons at this time. Check back later!")
        return

    text = "🎟 *ACTIVE PROMOTIONAL COUPONS:*\n\n"
    for c in coupons:
        val = f"{c.discount_value}% OFF" if c.discount_type == 'PERCENTAGE' else f"${c.discount_value} OFF"
        text += f"• Code: `{c.code}` - *{val}*\n  (Min Order: `${c.minimum_order}`)\n\n"

    text += "Apply coupon code at checkout to claim your discount!"
    await message.answer(text, parse_mode="Markdown")
