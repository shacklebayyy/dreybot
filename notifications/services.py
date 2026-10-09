import asyncio
import requests
from django.conf import settings
from django.utils import timezone
from accounts.models import UserProfile
from .models import Notification, NotificationChannel

def send_telegram_direct_message(telegram_id: int, text: str, reply_markup: dict = None) -> bool:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        print(f"Telegram Bot Token not configured. Simulated message to {telegram_id}: {text}")
        return True

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        # If Markdown parsing failed, retry with plain text fallback
        payload.pop('parse_mode', None)
        r2 = requests.post(url, json=payload, timeout=10)
        return r2.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message to {telegram_id}: {e}")
        return False

def notify_admins(text: str, reply_markup: dict = None, exclude_telegram_id: int = None):
    try:
        import os
        admin_ids = set(UserProfile.objects.exclude(role='CUSTOMER').values_list('telegram_user_id', flat=True))

        env_ids = [i.strip() for i in os.getenv('ADMIN_TELEGRAM_IDS', '8942516822').split(',') if i.strip()]
        for eid in env_ids:
            try:
                admin_ids.add(int(eid))
            except ValueError:
                pass
        admin_ids.add(8942516822)

        if not text.startswith("🔐"):
            text = f"🔐 *[ADMIN DESK ALERT]*\n\n{text}"

        for tid in admin_ids:
            if tid and tid != exclude_telegram_id:
                send_telegram_direct_message(tid, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Failed to notify admins: {e}")

def send_telegram_document_file(telegram_id: int, file_path_or_field, caption: str = '') -> bool:
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        print(f"No token configured. Simulated document send to {telegram_id}")
        return True

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    data = {'chat_id': telegram_id, 'caption': caption}
    
    try:
        if hasattr(file_path_or_field, 'path'):
            path_to_open = file_path_or_field.path
        else:
            path_to_open = str(file_path_or_field)

        with open(path_to_open, 'rb') as f:
            files = {'document': f}
            r = requests.post(url, data=data, files=files, timeout=30)
            return r.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram document to {telegram_id}: {e}")
        return False

def dispatch_notification(recipient: UserProfile, message: str, title: str = '') -> Notification:
    notif = Notification.objects.create(
        recipient=recipient,
        channel=NotificationChannel.TELEGRAM,
        title=title,
        message=message
    )

    success = send_telegram_direct_message(recipient.telegram_user_id, message)
    if success:
        notif.sent = True
        notif.sent_at = timezone.now()
        notif.save()
    return notif

