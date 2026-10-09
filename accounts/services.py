import os
from django.utils import timezone
from .models import UserProfile, UserRole
from django.contrib.auth.models import User

def get_or_create_telegram_user(telegram_id: int, username: str = '', first_name: str = '', last_name: str = '', language_code: str = 'en') -> UserProfile:
    admin_ids = [i.strip() for i in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if i.strip()]
    admin_users = [u.strip().lstrip('@').lower() for u in os.getenv('ADMIN_TELEGRAM_USERNAMES', '').split(',') if u.strip()]

    is_env_admin = str(telegram_id) in admin_ids or (username and username.lower() in admin_users)
    
    is_django_admin = False
    if username:
        is_django_admin = User.objects.filter(username=username, is_staff=True).exists()

    initial_role = UserRole.SUPER_ADMIN if (is_env_admin or is_django_admin) else UserRole.CUSTOMER

    profile, created = UserProfile.objects.get_or_create(
        telegram_user_id=telegram_id,
        defaults={
            'username': username or '',
            'first_name': first_name or '',
            'last_name': last_name or '',
            'language': language_code or 'en',
            'role': initial_role,
        }
    )

    updated = False
    if (is_env_admin or is_django_admin) and profile.role != UserRole.SUPER_ADMIN:
        profile.role = UserRole.SUPER_ADMIN
        updated = True

    if not created:
        if username and profile.username != username:
            profile.username = username
            updated = True
        if first_name and profile.first_name != first_name:
            profile.first_name = first_name
            updated = True
        if last_name and profile.last_name != last_name:
            profile.last_name = last_name
            updated = True
        profile.last_seen_at = timezone.now()

    if updated:
        profile.save()

    return profile

def promote_to_admin(telegram_id: int, role: str = UserRole.SUPER_ADMIN) -> UserProfile:
    profile = get_or_create_telegram_user(telegram_id=telegram_id)
    profile.role = role
    profile.save()
    return profile

