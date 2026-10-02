# DreyDocs - Learning Documents & Verification Services Platform

DreyDocs is a production-ready Telegram marketplace and authorized verification service platform powered by Django, PostgreSQL, Redis, Celery, aiogram 3.x, and a modern Tailwind CSS + Alpine.js + Chart.js admin web dashboard.

---

## 🌟 Key Features

1. **Telegram Marketplace Bot (`aiogram 3.x`)**:
   - `📄 ID MOCKUPS` - Country selection & educational template downloads.
   - `🛂 PASSPORT MOCKUPS` - Country passport templates.
   - `🚗 DRIVER LICENSE MOCKUPS` - All 50 US States dynamic menu.
   - `🏢 BUSINESS DOCUMENTS` & `🎓 CERTIFICATES` & `📚 OTHER TEMPLATES`.
   - `🔎 VERIFICATION SERVICES` - EIN, TIN, SSN, Identity, Employment checks with explicit consent logging and masked output.
   - `🛒 MY ORDERS` & `👤 MY ACCOUNT` & `🎟 COUPONS` & `💬 SUPPORT` & `🔍 SEARCH`.

2. **Payment Provider Abstraction Layer**:
   - Integrated support for **Stripe**, **Paystack**, **M-Pesa**, **Crypto USDT / BTC**, and **Development Mock** payments.

3. **Secure Download System**:
   - Private media file storage with expiring, single-use download tokens.
   - Direct physical file paths (`/media/products/`) are blocked from public HTTP access.

4. **Compliance & Safety Controls**:
   - Automatic watermark disclaimers on all document mockups: `SAMPLE`, `EDUCATIONAL MOCKUP`, `NOT A GOVERNMENT DOCUMENT`, `NOT VALID FOR IDENTIFICATION`.
   - Data minimization and masking for all sensitive identity/verification checks (e.g. `***-**-1234`).
   - Audit log tracking for all sensitive data access and administrative actions.

5. **Powerful Admin Web Dashboard (`/admin-panel/`)**:
   - Real-time revenue, order, customer, and verification analytics charts using Chart.js.
   - Dynamic product upload, category management, country/state configuration, customer blocking/notifications, and verification provider credentials management.

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- PostgreSQL (or SQLite for quick testing)
- Redis

### 2. Environment Setup
```bash
git clone <repository_url>
cd bot

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 3. Database Migrations & Initial Seed Data
```bash
python manage.py makemigrations
python manage.py migrate

# Seed initial categories, countries, 50 US states, sample products, and verification services
python manage.py seed_data

# Create Django Superuser for Web Admin Access
python manage.py createsuperuser
```

### 4. Running Application Services

#### A. Run Django Web Server
```bash
python manage.py runserver 0.0.0.0:8000
```
- Landing Page: `http://localhost:8000/`
- Admin Dashboard: `http://localhost:8000/admin-panel/`
- Django Default Admin: `http://localhost:8000/admin/`

#### B. Run DreyDocs Telegram Bot
```bash
python telegram_bot/bot.py
```

#### C. Run Celery Worker & Beat (Optional for Background Tasks)
```bash
celery -A drey_docs worker -l info
celery -A drey_docs beat -l info
```

---

## 🐳 Docker Deployment

To launch the complete production stack (Django Web, Telegram Bot, Celery Worker, Celery Beat, PostgreSQL, Redis, Nginx):

```bash
docker compose up -d --build
```

Run seed data inside Docker container:
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_data
```

---

## 🧪 Running Automated Test Suite

```bash
python -m pytest
```

Or using Django test runner:
```bash
python manage.py test tests
```

---

## 📜 Systemd Service Configuration (Ubuntu VPS Deployment)

### 1. Web Service (`/etc/systemd/system/dreydocs-web.service`)
```ini
[Unit]
Description=DreyDocs Web Gunicorn Application
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/dreydocs
ExecStart=/var/www/dreydocs/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 drey_docs.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Telegram Bot Service (`/etc/systemd/system/dreydocs-bot.service`)
```ini
[Unit]
Description=DreyDocs Telegram Bot Daemon
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/dreydocs
ExecStart=/var/www/dreydocs/venv/bin/python telegram_bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🛡 Security & Compliance Disclaimer

DreyDocs is strictly designed for **educational document design templates** and **authorized verification services**. The platform contains strict compliance controls preventing the creation or distribution of authentic government identification documents.
