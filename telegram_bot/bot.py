import os
import sys
import asyncio
import logging
import django

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drey_docs.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.conf import settings
from aiogram import Bot, Dispatcher
from telegram_bot.handlers import (
    start, catalog, cart_order, verification, account, support, coupons, search, admin
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token or token == '123456789:ABCdefGHIjklMNOpqrsTUVwxyz':
        logger.warning("No valid TELEGRAM_BOT_TOKEN configured in .env. Bot will start in dry-run monitoring mode.")
        print("Please configure TELEGRAM_BOT_TOKEN in .env to connect live with Telegram servers.")
        return

    bot = Bot(token=token)
    dp = Dispatcher()

    # Include Routers
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(catalog.router)
    dp.include_router(cart_order.router)
    dp.include_router(verification.router)
    dp.include_router(account.router)
    dp.include_router(coupons.router)
    dp.include_router(search.router)
    dp.include_router(support.router)

from aiogram.types import BotCommand

    # Register Bot Commands for Telegram UI Menu Button
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="🚀 Main Menu & Welcome"),
            BotCommand(command="menu", description="📱 Open Main Menu Keyboard"),
            BotCommand(command="cc", description="💳 CC Service ($20.00)"),
            BotCommand(command="search", description="🔍 Search Templates & Services"),
            BotCommand(command="cancel", description="❌ Cancel Current Operation")
        ])
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")

    logger.info("DreyDocs Telegram Bot starting long polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
