from .models import SystemSetting

def system_settings(request):
    return {
        'site_name': SystemSetting.get_setting('site_name', 'DreyDocs'),
        'tagline': SystemSetting.get_setting('tagline', 'Learning Documents & Verification Services'),
        'telegram_bot_username': SystemSetting.get_setting('telegram_bot_username', 'DreyDocsBot'),
        'support_username': SystemSetting.get_setting('support_username', 'DreyDocsSupport'),
    }
