from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.core.files.base import ContentFile
from .models import Report, ReportResult
from .pdf_generator import build_report_pdf
from notifications.utils import notify
from notifications.models import Notification
from staff.decorators import staff_or_admin_required
from appointments.models import Appointment
from tests_app.models import DiagnosticTest
from django.core.mail import send_mail
from django.conf import settings

MAX_UPLOAD_SIZE_BYTES = 15 * 1024 * 1024


@login_required
def my_reports_view(request):
    if request.user.role != 'PATIENT':
        return redirect('dashboard_redirect')
    reports = Report.objects.filter(patient__user=request.user, status=Report.Status.READY)
    return render(request, 'reports/my_reports.html', {'reports': reports})


@login_required
def report_detail_view(request, report_uid):
    report = get_object_or_404(Report, report_uid=report_uid)
    if request.user.role == 'PATIENT' and report.patient.user != request.user:
        raise Http404("Report not found.")
    return render(request, 'reports/report_detail.html', {'report': report})


@login_required
def report_download_view(request, report_uid):
    report = get_object_or_404(Report, report_uid=report_uid)
    if request.user.role == 'PATIENT' and report.patient.user != request.user:
        raise Http404("Report not found.")
    if not report.pdf_file:
        messages.error(request, "This report's PDF hasn't been generated yet.")
        return redirect('report_detail', report_uid=report_uid)
    return FileResponse(
        report.pdf_file.open('rb'), as_attachment=True,
        filename=f"{report.appointment.appointment_id}_{report.patient.patient_id}.pdf"
    )

@login_required
def generate_report_pdf_view(request, report_uid):
    if request.user.role not in ['STAFF', 'ADMIN']:
        messages.error(request, "You don't have permission to generate reports.")
        return redirect('dashboard_redirect')

    report = get_object_or_404(Report, report_uid=report_uid)

    if report.origin == Report.Origin.UPLOADED:
        messages.error(request, "This report was uploaded directly — it cannot be system-generated.")
        return redirect('staff_report_detail', report_uid=report.report_uid)

    pdf_buffer = build_report_pdf(report)
    filename = f"{report.appointment.appointment_id}_{report.patient.patient_id}.pdf"
    report.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=False)
    report.status = Report.Status.READY
    report.save()

    patient_user = report.patient.user
    test_names = ", ".join(r.test.name for r in report.results.all())

    notify(
        recipient=patient_user,
        title="Report Ready",
        message=f"Your report for {report.appointment.appointment_id} ({test_names}) is now available.",
        notification_type=Notification.NotificationType.REPORT_READY,
        link_url=f"/reports/{report.report_uid}/",
    )

    _send_report_ready_email(request, report, patient_user)

    messages.success(request, f"PDF generated for {report.report_uid}.")
    return redirect('report_detail', report_uid=report.report_uid)


@staff_or_admin_required
def staff_report_list_view(request):
    return render(request, 'reports/staff_report_list.html', {'reports': Report.objects.all()})


def _reportable_tests_for_appointment(appointment):
    """Union of directly-booked tests and tests included via any booked
    package, deduplicated by ID — the single source of truth used both
    to auto-populate results AND to validate any submitted test_id."""
    direct_ids = appointment.tests.values_list('id', flat=True)
    package_test_ids = DiagnosticTest.objects.filter(
        packages__in=appointment.packages.all()
    ).values_list('id', flat=True)
    return DiagnosticTest.objects.filter(id__in=set(direct_ids) | set(package_test_ids))


def _get_or_create_report(appointment, request_user):
    report, created = Report.objects.get_or_create(
        appointment=appointment,
        defaults={'patient': appointment.patient, 'generated_by': request_user},
    )
    return report, created

def _send_report_ready_email(request, report, patient_user):
    """
    Sent once, right after a report's PDF is generated or an external
    PDF is uploaded. fail_silently=True is deliberate: an SMTP failure
    must never block report generation itself — the report is already
    saved and the in-app notification already fired regardless.
    """
    if not patient_user.email:
        return

    download_url = request.build_absolute_uri(f"/reports/{report.report_uid}/")

    message = (
        f"Dear {patient_user.get_full_name() or patient_user.username},\n\n"
        f"Your LifeCare Diagnostic Center report for appointment "
        f"{report.appointment.appointment_id} is now ready.\n\n"
        f"You can view and download your report by logging in here:\n{download_url}\n\n"
        f"For your privacy, the report itself is not attached to this email — "
        f"please log in to your LifeCare account to view or download it securely.\n\n"
        f"— LIFE CARE DIAGNOSTIC CENTER"
    )

    send_mail(
        subject=f"LifeCare Report Ready — {report.appointment.appointment_id}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[patient_user.email],
        fail_silently=True,
    )


@staff_or_admin_required
def staff_report_choice_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    existing = Report.objects.filter(appointment=appointment).first()
    if existing:
        return redirect('staff_report_detail', report_uid=existing.report_uid)

    if not _reportable_tests_for_appointment(appointment).exists():
        messages.error(request, "This appointment has no tests to report on.")
        return redirect('staff_appointment_detail', appointment_id=appointment.appointment_id)

    return render(request, 'reports/staff_report_choice.html', {'appointment': appointment})


@staff_or_admin_required
def staff_report_create_view(request, appointment_id):
    """
    THIS is the function responsible for multi-test population. It does
    NOT read a single 'test' field from POST — it creates one
    ReportResult per booked test automatically, then redirects straight
    into the detail page where every test gets its own input section.
    """
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    reportable_tests = _reportable_tests_for_appointment(appointment)

    if not reportable_tests.exists():
        messages.error(request, "This appointment has no tests to report on.")
        return redirect('staff_appointment_detail', appointment_id=appointment.appointment_id)

    report, created = _get_or_create_report(appointment, request.user)
    report.origin = Report.Origin.GENERATED
    report.save()

    existing_test_ids = set(report.results.values_list('test_id', flat=True))
    new_results = [
        ReportResult(report=report, test=t)
        for t in reportable_tests if t.id not in existing_test_ids
    ]
    if new_results:
        ReportResult.objects.bulk_create(new_results)

    if created:
        messages.success(request, f"Report created for {appointment.appointment_id} with {reportable_tests.count()} test(s). Enter results below.")
    return redirect('staff_report_detail', report_uid=report.report_uid)


@staff_or_admin_required
def staff_report_upload_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    if request.method == 'POST':
        uploaded_file = request.FILES.get('report_file')
        referred_by = request.POST.get('referred_by', '').strip()
        is_demo_data = request.POST.get('is_demo_data') == 'on'

        if not uploaded_file or not uploaded_file.name.lower().endswith('.pdf') \
                or uploaded_file.content_type != 'application/pdf':
            messages.error(request, "Please upload a valid PDF file.")
            return render(request, 'reports/staff_report_upload.html', {'appointment': appointment})


        if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
            messages.error(request, "File is too large (max 15 MB).")
            return render(request, 'reports/staff_report_upload.html', {'appointment': appointment})

        report, created = _get_or_create_report(appointment, request.user)
        report.origin = Report.Origin.UPLOADED
        report.referred_by = referred_by
        report.is_demo_data = is_demo_data
        report.status = Report.Status.READY
        report.pdf_file = uploaded_file
        report.save()

        notify(
            recipient=appointment.patient.user,
            title="Report Ready",
            message=f"Your report for {appointment.appointment_id} is now available.",
            notification_type=Notification.NotificationType.REPORT_READY,
            link_url=f"/reports/{report.report_uid}/",
        )

        _send_report_ready_email(request, report, appointment.patient.user)

        messages.success(request, "Report uploaded successfully.")
        return redirect('staff_report_detail', report_uid=report.report_uid)

    return render(request, 'reports/staff_report_upload.html', {'appointment': appointment})


@staff_or_admin_required
def staff_report_detail_view(request, report_uid):
    report = get_object_or_404(Report, report_uid=report_uid)

    # Self-healing: guarantee every currently-booked test has a
    # ReportResult row, no matter how this Report was originally
    # created (staff flow, admin panel, or otherwise). Idempotent —
    # only adds rows that don't already exist; never duplicates or
    # touches values already entered.
    if report.origin == Report.Origin.GENERATED:
        reportable_tests = _reportable_tests_for_appointment(report.appointment)
        existing_test_ids = set(report.results.values_list('test_id', flat=True))
        missing = [
            ReportResult(report=report, test=t)
            for t in reportable_tests if t.id not in existing_test_ids
        ]
        if missing:
            ReportResult.objects.bulk_create(missing)

    if request.method == 'POST':
        print("=== REPORT POST RECEIVED ===")
        print(request.POST)

        if report.origin == Report.Origin.UPLOADED:
            messages.error(request, "This report was uploaded directly and has no fillable fields.")
            return redirect('staff_report_detail', report_uid=report.report_uid)

        report.is_demo_data = request.POST.get('is_demo_data') == 'on'
        report.referred_by = request.POST.get('referred_by', '').strip()
        report.save()

        for result in report.results.all():
            prefix = f"result_{result.id}_"
            result.result_value = request.POST.get(prefix + 'value', '').strip()
            result.reference_range = request.POST.get(prefix + 'range', '').strip()
            result.units = request.POST.get(prefix + 'units', '').strip()
            result.abnormal_flag = request.POST.get(prefix + 'flag', 'NORMAL')
            result.save()

        messages.success(request, f"Saved results for {report.results.count()} test(s).")
        return redirect('staff_report_detail', report_uid=report.report_uid)

    return render(request, 'reports/staff_report_detail.html', {'report': report})