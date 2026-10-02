from django.utils import timezone
from .models import UserProfile, UserRole

def get_or_create_telegram_user(telegram_id: int, username: str = '', first_name: str = '', last_name: str = '', language_code: str = 'en') -> UserProfile:
    profile, created = UserProfile.objects.get_or_create(
        telegram_user_id=telegram_id,
        defaults={
            'username': username or '',
            'first_name': first_name or '',
            'last_name': last_name or '',
            'language': language_code or 'en',
            'role': UserRole.CUSTOMER,
        }
    )
    if not created:
        updated = False
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
        profile.save()
    return profile
