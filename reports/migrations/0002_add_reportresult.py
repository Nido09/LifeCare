from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_value', models.CharField(blank=True, max_length=255)),
                ('reference_range', models.CharField(blank=True, max_length=255)),
                ('units', models.CharField(blank=True, max_length=50)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='reports.report')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='report_results', to='tests_app.diagnostictest')),
            ],
            options={'ordering': ['test__name']},
        ),
        migrations.AlterUniqueTogether(
            name='reportresult',
            unique_together={('report', 'test')},
        ),
    ]