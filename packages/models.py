from django.db import models
from tests_app.models import DiagnosticTest


class HealthPackage(models.Model):
    name = models.CharField(max_length=255)
    package_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    tests_included = models.ManyToManyField(DiagnosticTest, related_name='packages', blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.package_code})"