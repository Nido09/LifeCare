from django.db import models
from appointments.models import Appointment
from accounts.models import User


class HomeCollectionRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        OUT_FOR_COLLECTION = 'OUT_FOR_COLLECTION', 'Out for Collection'
        COLLECTED = 'COLLECTED', 'Collected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    request_id = models.CharField(max_length=20, unique=True, editable=False)

    # One appointment can have at most one home collection request tied to it.
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='home_collection')

    assigned_staff = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role': 'STAFF'},
        related_name='assigned_collections'
    )

    status = models.CharField(max_length=25, choices=Status.choices, default=Status.REQUESTED)

    contact_number = models.CharField(max_length=15)
    address = models.TextField()
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()

    collected_at = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.request_id:
            last = HomeCollectionRequest.objects.order_by('id').last()
            next_num = 1 if not last else last.id + 1
            self.request_id = f"LC-HC-{next_num:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_id} ({self.status})"

    class Meta:
        ordering = ['-created_at']

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=HomeCollectionRequest)
def notify_on_collection_status_change(sender, instance, created, **kwargs):
    if created:
        return  # don't notify on the initial creation, only on later updates

    from notifications.utils import notify
    from notifications.models import Notification

    status_messages = {
        HomeCollectionRequest.Status.ASSIGNED: "A collection agent has been assigned to your home sample pickup.",
        HomeCollectionRequest.Status.OUT_FOR_COLLECTION: "Our agent is on the way to collect your sample.",
        HomeCollectionRequest.Status.COLLECTED: "Your sample has been collected successfully.",
        HomeCollectionRequest.Status.CANCELLED: "Your home collection request has been cancelled.",
    }

    message = status_messages.get(instance.status)
    if message:
        notify(
            recipient=instance.appointment.patient.user,
            title=f"Home Collection: {instance.get_status_display()}",
            message=message,
            notification_type=Notification.NotificationType.SAMPLE_COLLECTION,
            link_url=f"/appointments/{instance.appointment.appointment_id}/",
        )