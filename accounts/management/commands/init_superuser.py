import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Creates a superuser automatically if none exists, using environment variables or defaults."

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@dreydocs.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin12345!')

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("Superuser already exists in the database."))
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}' ({email})."))
        else:
            u = User.objects.get(username=username)
            u.is_superuser = True
            u.is_staff = True
            u.set_password(password)
            u.save()
            self.stdout.write(self.style.SUCCESS(f"Promoted existing user '{username}' to superuser."))
