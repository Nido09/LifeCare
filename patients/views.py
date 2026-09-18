import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from .models import PatientProfile
from appointments.models import Appointment
from reports.models import Report
from notifications.models import Notification
from payments.models import Payment


@login_required
def patient_dashboard_view(request):
    if request.user.role != 'PATIENT':
        messages.error(request, "That page is only available to patient accounts.")
        return redirect('dashboard_redirect')

    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    appointments = Appointment.objects.filter(patient=profile)

    upcoming = appointments.filter(
        preferred_date__gte=timezone.now().date(),
        status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
    ).order_by('preferred_date').first()

    # ---- Chart data (all from real DB rows, never fabricated) ----

    # Appointments over time (last 6 months)
    monthly = (
        appointments.annotate(month=TruncMonth('created_at'))
        .values('month').annotate(count=Count('id')).order_by('month')
    )
    appts_labels = [m['month'].strftime('%b %Y') for m in monthly]
    appts_data = [m['count'] for m in monthly]

    # Appointment status breakdown
    status_qs = appointments.values('status').annotate(count=Count('id'))
    status_labels = [dict(Appointment.Status.choices)[s['status']] for s in status_qs]
    status_data = [s['count'] for s in status_qs]

    # Tests booked by department
    dept_qs = (
        appointments.values('tests__category__name')
        .exclude(tests__category__name__isnull=True)
        .annotate(count=Count('tests'))
        .order_by('-count')
    )
    dept_labels = [d['tests__category__name'] for d in dept_qs]
    dept_data = [d['count'] for d in dept_qs]

    # Spending history (paid payments only, grouped by month)
    spend_qs = (
        Payment.objects.filter(appointment__patient=profile, status=Payment.Status.PAID)
        .annotate(month=TruncMonth('paid_at'))
        .values('month').annotate(total=Sum('amount')).order_by('month')
    )
    spend_labels = [s['month'].strftime('%b %Y') for s in spend_qs if s['month']]
    spend_data = [float(s['total']) for s in spend_qs if s['month']]

    total_spent = Payment.objects.filter(
        appointment__patient=profile, status=Payment.Status.PAID
    ).aggregate(t=Sum('amount'))['t'] or 0

    context = {
        'profile': profile,
        'upcoming_appointment': upcoming,
        'appointment_count': appointments.count(),
        'pending_appointments': appointments.filter(status=Appointment.Status.PENDING).count(),
        'completed_appointments': appointments.filter(status=Appointment.Status.COMPLETED).count(),
        'cancelled_appointments': appointments.filter(status=Appointment.Status.CANCELLED).count(),
        'available_reports': Report.objects.filter(patient=profile, status=Report.Status.READY).count(),
        'total_spent': total_spent,
        'pending_payments': appointments.exclude(status=Appointment.Status.CANCELLED)
            .exclude(payments__status=Payment.Status.PAID).count(),
        'unread_notifications': Notification.objects.filter(recipient=request.user, is_read=False).count(),
        'recent_payments': Payment.objects.filter(appointment__patient=profile).order_by('-created_at')[:5],

        'chart_appts_labels': json.dumps(appts_labels),
        'chart_appts_data': json.dumps(appts_data),
        'chart_status_labels': json.dumps(status_labels),
        'chart_status_data': json.dumps(status_data),
        'chart_dept_labels': json.dumps(dept_labels),
        'chart_dept_data': json.dumps(dept_data),
        'chart_spend_labels': json.dumps(spend_labels),
        'chart_spend_data': json.dumps(spend_data),
    }
    return render(request, 'patients/dashboard.html', context)


@login_required
def patient_profile_view(request):
    if request.user.role != 'PATIENT':
        return redirect('dashboard_redirect')

    profile, created = PatientProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.phone_number = request.POST.get('phone_number', '').strip()
        request.user.save()

        profile.date_of_birth = request.POST.get('date_of_birth') or None
        profile.gender = request.POST.get('gender', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('patient_profile')

    return render(request, 'patients/profile.html', {'profile': profile})