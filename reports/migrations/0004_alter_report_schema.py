from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_migrate_report_data'),
    ]

    operations = [
        migrations.RemoveField(model_name='report', name='test'),
        migrations.RemoveField(model_name='report', name='result_value'),
        migrations.RemoveField(model_name='report', name='reference_range'),
        migrations.RemoveField(model_name='report', name='units'),
        migrations.AlterField(
            model_name='report',
            name='appointment',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='appointments.appointment'),
        ),
    ]