from django.db import models
from accounts.models import UserProfile

class NotificationChannel(models.TextChoices):
    TELEGRAM = 'TELEGRAM', 'Telegram'
    EMAIL = 'EMAIL', 'Email'
    SMS = 'SMS', 'SMS'

class Notification(models.Model):
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.TELEGRAM)
    title = models.CharField(max_length=255, blank=True, default='')
    message = models.TextField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient} via {self.channel}"
