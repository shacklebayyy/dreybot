#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Ensure superuser exists
python manage.py init_superuser

# Seed initial system data (categories, countries, 50 US states)
python manage.py seed_data
