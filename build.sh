#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations if database is available during build
python manage.py migrate --no-input || echo "===> Note: Build-time migrations skipped; run.sh will execute migrations on startup."

# Ensure superuser exists
python manage.py init_superuser || true

# Seed initial system data (categories, countries, 50 US states)
python manage.py seed_data || true
