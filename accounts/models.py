from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        STAFF = 'STAFF', 'Staff'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT)
    phone_number = models.CharField(max_length=15, blank=True)
    country_code = models.CharField(max_length=5, blank=True, default='+91')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} — {self.name}"


class HomeCollectionInquiry(models.Model):
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    preferred_date = models.DateField(null=True, blank=True)
    address = models.TextField()
    notes = models.TextField(blank=True)
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.phone_number}"


class Feedback(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    class Rating(models.IntegerChoices):
        ONE = 1, '1 - Poor'
        TWO = 2, '2 - Fair'
        THREE = 3, '3 - Good'
        FOUR = 4, '4 - Very Good'
        FIVE = 5, '5 - Excellent'

    # Linked to an existing account when the submitter is logged in —
    # NEVER a new/duplicate patient record. Null for guest submissions.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_entries')
    guest_name = models.CharField(max_length=150, blank=True)
    guest_email = models.EmailField(blank=True)

    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    comment = models.TextField()

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def display_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name or 'Anonymous'

    def __str__(self):
        return f"{self.display_name()} — {self.rating}★ ({self.status})"

    class Meta:
        ordering = ['-created_at']