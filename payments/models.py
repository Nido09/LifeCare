from django.db import models
from appointments.models import Appointment


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'     # Razorpay order created, not yet paid
        PAID = 'PAID', 'Paid'               # Verified successful payment
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    payment_id = models.CharField(max_length=20, unique=True, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)

    # Razorpay's own identifiers — these come FROM Razorpay, we never invent them.
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            last = Payment.objects.order_by('id').last()
            next_num = 1 if not last else last.id + 1
            self.payment_id = f"LC-PAY-{next_num:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_id} — {self.status} — ₹{self.amount}"

    class Meta:
        ordering = ['-created_at']

    class Method(models.TextChoices):
        ONLINE = 'ONLINE', 'Online (Razorpay)'
        PAY_AT_LAB = 'PAY_AT_LAB', 'Pay at Lab'

    payment_method = models.CharField(max_length=15, choices=Method.choices, default=Method.ONLINE)