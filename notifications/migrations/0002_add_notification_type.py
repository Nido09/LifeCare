from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('APPOINTMENT', 'Appointment'),
                    ('STATUS_CHANGE', 'Status Change'),
                    ('SAMPLE_COLLECTION', 'Sample Collection'),
                    ('REPORT_READY', 'Report Ready'),
                    ('PAYMENT', 'Payment'),
                    ('GENERAL', 'General')
                ],
                default='GENERAL',
                max_length=20
            ),
        ),
    ]