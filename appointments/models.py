from django.db import models
from patients.models import PatientProfile
from tests_app.models import DiagnosticTest
from packages.models import HealthPackage


class Appointment(models.Model):
    class CollectionType(models.TextChoices):
        LAB_VISIT = 'LAB_VISIT', 'Lab Visit'
        HOME_COLLECTION = 'HOME_COLLECTION', 'Home Collection'

    class PaymentPreference(models.TextChoices):
        ONLINE = 'ONLINE', 'Pay Online Now'
        PAY_AT_LAB = 'PAY_AT_LAB', 'Pay at Lab / After Test'

    payment_preference = models.CharField(
        max_length=15, choices=PaymentPreference.choices, default=PaymentPreference.PAY_AT_LAB
    )

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        SAMPLE_COLLECTED = 'SAMPLE_COLLECTED', 'Sample Collected'
        PROCESSING = 'PROCESSING', 'Processing'
        REPORT_READY = 'REPORT_READY', 'Report Ready'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    appointment_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')

    tests = models.ManyToManyField(DiagnosticTest, blank=True, related_name='appointments')
    packages = models.ManyToManyField(HealthPackage, blank=True, related_name='appointments')

    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    collection_type = models.CharField(max_length=20, choices=CollectionType.choices)
    address = models.TextField(blank=True, help_text="Required only for home collection")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            last = Appointment.objects.order_by('id').last()
            next_num = 1 if not last else last.id + 1
            self.appointment_id = f"LC-AP-{next_num:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.patient_id} ({self.status})"

    class Meta:
        ordering = ['-created_at']