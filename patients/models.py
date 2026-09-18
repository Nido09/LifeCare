from django.db import models
from django.utils import timezone
from accounts.models import User


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    area = models.CharField(max_length=100, blank=True, help_text="Mumbai locality selected at registration.")
    country = models.CharField(max_length=50, blank=True, default='India')
    state = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last = PatientProfile.objects.order_by('id').last()
            next_num = 1 if not last else last.id + 1
            self.patient_id = f"LC-P-{next_num:05d}"
        super().save(*args, **kwargs)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years

    def __str__(self):
        return f"{self.patient_id} - {self.user.get_full_name() or self.user.username}"