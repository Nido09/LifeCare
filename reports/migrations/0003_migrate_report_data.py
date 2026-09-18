from django.db import migrations


def migrate_reports_forward(apps, schema_editor):
    Report = apps.get_model('reports', 'Report')
    ReportResult = apps.get_model('reports', 'ReportResult')

    # Group existing Report rows by appointment_id
    from collections import defaultdict
    by_appointment = defaultdict(list)
    for report in Report.objects.all().order_by('created_at'):
        by_appointment[report.appointment_id].append(report)

    for appointment_id, reports in by_appointment.items():
        surviving = reports[0]

        any_ready = any(r.status == 'READY' for r in reports)
        all_real = all(r.is_demo_data is False for r in reports)

        for r in reports:
            ReportResult.objects.create(
                report=surviving,
                test_id=r.test_id,
                result_value=r.result_value,
                reference_range=r.reference_range,
                units=r.units,
            )

        # Consolidate report-level flags across the merged rows.
        surviving.is_demo_data = not all_real
        # Old single-test PDFs can't represent the new multi-test format —
        # reset to PENDING so staff regenerate one consolidated PDF.
        surviving.pdf_file = None
        surviving.status = 'PENDING'
        surviving.save()

        # Remove the now-redundant duplicate Report rows for this
        # appointment (their data has already been copied above).
        for r in reports[1:]:
            r.delete()


def migrate_reports_backward(apps, schema_editor):
    # Not reversible — old per-test Report rows are gone by design.
    raise migrations.exceptions.IrreversibleError(
        "This migration cannot be reversed: original per-test Report rows were consolidated."
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_add_reportresult'),
    ]

    operations = [
        migrations.RunPython(migrate_reports_forward, migrate_reports_backward),
    ]