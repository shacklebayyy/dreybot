#!/usr/bin/env bash
# Start Telegram Bot in background
python telegram_bot/bot.py &

# Start Django Gunicorn Web Server
exec gunicorn drey_docs.wsgi:application
