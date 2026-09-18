from django.db import models
from accounts.models import User


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPOINTMENT = 'APPOINTMENT', 'Appointment'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Change'
        SAMPLE_COLLECTION = 'SAMPLE_COLLECTION', 'Sample Collection'
        REPORT_READY = 'REPORT_READY', 'Report Ready'
        PAYMENT = 'PAYMENT', 'Payment'
        GENERAL = 'GENERAL', 'General'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.GENERAL)

    title = models.CharField(max_length=200)
    message = models.TextField()

    # Optional link so clicking a notification can take the user
    # straight to the relevant appointment/report, if applicable.
    link_url = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.recipient.username}"