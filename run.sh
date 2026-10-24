#!/usr/bin/env bash
# Exit on error
set -o errexit

PORT="${PORT:-8000}"

# 1. Always run database migrations and seed data FIRST before starting services
echo "===> Applying database migrations..."
python manage.py migrate --no-input

echo "===> Ensuring admin superuser..."
python manage.py init_superuser

echo "===> Seeding system data..."
python manage.py seed_data

# 2. Start Telegram Bot in background
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-9108786947:AAHIdbTs2u0rtfsZhEsy6jwcIbLwz7dqNl4}"
export TELEGRAM_BOT_USERNAME="${TELEGRAM_BOT_USERNAME:-Dreynewbot}"
echo "===> Starting Telegram Bot worker in background (@$TELEGRAM_BOT_USERNAME)..."
python telegram_bot/bot.py &

# 3. Start Django Gunicorn Web Server
echo "===> Starting Gunicorn web server on 0.0.0.0:$PORT..."
exec gunicorn --bind "0.0.0.0:$PORT" drey_docs.wsgi:application
