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

# 2. Start Telegram Bot in background if configured
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "===> Starting Telegram Bot worker in background..."
    python telegram_bot/bot.py &
else
    echo "===> TELEGRAM_BOT_TOKEN not provided; skipping Telegram bot worker."
fi

# 3. Start Django Gunicorn Web Server
echo "===> Starting Gunicorn web server on 0.0.0.0:$PORT..."
exec gunicorn --bind "0.0.0.0:$PORT" drey_docs.wsgi:application
