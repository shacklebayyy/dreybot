import random
import string
from django.db import models
from django.utils import timezone
from accounts.models import UserProfile

class TicketStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    WAITING_CUSTOMER = 'WAITING_CUSTOMER', 'Waiting Customer'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'

def generate_ticket_number():
    date_str = timezone.now().strftime('%Y%m%d')
    rand_str = ''.join(random.choices(string.digits, k=5))
    return f"TCK-{date_str}-{rand_str}"

class SupportTicket(models.Model):
    ticket_number = models.CharField(max_length=32, unique=True, default=generate_ticket_number, db_index=True)
    customer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=25, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    assigned_admin = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Ticket #{self.ticket_number} - {self.subject} ({self.status})"

class SupportMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    is_admin_reply = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on #{self.ticket.ticket_number} by {self.sender}"
