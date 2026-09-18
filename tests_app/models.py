from django.db import models


class TestCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class DiagnosticTest(models.Model):
    name = models.CharField(max_length=255)
    test_code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(TestCategory, on_delete=models.PROTECT, related_name='tests')
    description = models.TextField(blank=True)
    sample_type = models.CharField(max_length=100, blank=True)
    preparation_instructions = models.TextField(blank=True)
    is_fasting_required = models.BooleanField(default=False)
    fasting_instructions = models.CharField(
        max_length=255, blank=True,
        help_text="e.g. '8-12 hours fasting required'. Only shown if fasting is required above."
    )
    turnaround_time_hours = models.PositiveIntegerField(default=24)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=['test_code']), models.Index(fields=['name'])]

    def __str__(self):
        return f"{self.name} ({self.test_code})"