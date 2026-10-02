from django.core.management.base import BaseCommand
from accounts.models import UserProfile, UserRole

class Command(BaseCommand):
    help = "Promote a Telegram user to SUPER_ADMIN role so they receive admin push notifications and commands."

    def add_arguments(self, parser):
        parser.add_argument('target', type=str, help='Telegram User ID or Username (without @)')

    def handle(self, *args, **options):
        target = options['target'].strip().lstrip('@')

        profile = None
        if target.isdigit():
            profile = UserProfile.objects.filter(telegram_user_id=int(target)).first()

        if not profile:
            profile = UserProfile.objects.filter(username__iexact=target).first()

        if not profile:
            self.stderr.write(self.style.ERROR(f"No UserProfile found matching ID or Username '{target}'. Make sure the user has sent /start to the bot first!"))
            return

        profile.role = UserRole.SUPER_ADMIN
        profile.save()

        name = profile.full_name
        self.stdout.write(self.style.SUCCESS(f"Successfully promoted '{name}' (ID: {profile.telegram_user_id}) to SUPER_ADMIN! Admin push notifications enabled."))
