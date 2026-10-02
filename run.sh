#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Always run database migrations and seed data FIRST before starting services
python manage.py migrate --no-input
python manage.py init_superuser
python manage.py seed_data

# 2. Start Telegram Bot in background
python telegram_bot/bot.py &

# 3. Start Django Gunicorn Web Server
exec gunicorn drey_docs.wsgi:application
