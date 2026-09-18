from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
from .decorators import staff_or_admin_required, admin_required
from appointments.models import Appointment
from samples.models import HomeCollectionRequest
from reports.models import Report
from accounts.models import ContactMessage, HomeCollectionInquiry, User
from payments.models import Payment
import json
from django.db.models.functions import TruncMonth
from django.db.models.functions import TruncDate

@staff_or_admin_required
def staff_collection_list_view(request):
    status_filter = request.GET.get('status', '')
    requests_qs = HomeCollectionRequest.objects.all()

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    context = {
        'requests': requests_qs,
        'status_choices': HomeCollectionRequest.Status.choices,
        'selected_status': status_filter,
    }
    return render(request, 'samples/staff_collection_list.html', context)


@staff_or_admin_required
def staff_collection_detail_view(request, request_id):
    collection_request = get_object_or_404(HomeCollectionRequest, request_id=request_id)
    staff_users = User.objects.filter(role='STAFF')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        assigned_staff_id = request.POST.get('assigned_staff')
        staff_notes = request.POST.get('staff_notes', '').strip()

        valid_statuses = [choice[0] for choice in HomeCollectionRequest.Status.choices]
        if new_status in valid_statuses:
            collection_request.status = new_status

        if assigned_staff_id:
            collection_request.assigned_staff_id = assigned_staff_id
        else:
            collection_request.assigned_staff = None

        collection_request.staff_notes = staff_notes

        if new_status == HomeCollectionRequest.Status.COLLECTED and not collection_request.collected_at:
            collection_request.collected_at = timezone.now()

        collection_request.save()
        messages.success(request, "Collection request updated.")
        return redirect('staff_collection_detail', request_id=collection_request.request_id)

    context = {
        'collection_request': collection_request,
        'staff_users': staff_users,
        'status_choices': HomeCollectionRequest.Status.choices,
    }
    return render(request, 'samples/staff_collection_detail.html', context)

@staff_or_admin_required
def staff_dashboard_view(request):
    today = timezone.now().date()

    today_appointments = Appointment.objects.filter(preferred_date=today).exclude(status='CANCELLED')
    pending_appointments = Appointment.objects.filter(status=Appointment.Status.PENDING)
    samples_to_collect = HomeCollectionRequest.objects.filter(
        status__in=[HomeCollectionRequest.Status.REQUESTED, HomeCollectionRequest.Status.ASSIGNED]
    )
    processing_reports = Report.objects.filter(status=Report.Status.PENDING)
    reports_ready = Report.objects.filter(status=Report.Status.READY)
    home_collections = HomeCollectionRequest.objects.exclude(
        status__in=[HomeCollectionRequest.Status.COLLECTED, HomeCollectionRequest.Status.CANCELLED]
    )

    # Daily appointments — last 14 days, real counts only
    daily_qs = (
        Appointment.objects.annotate(day=TruncDate('created_at'))
        .values('day').annotate(count=Count('id')).order_by('day')[:14]
    )
    status_qs = Appointment.objects.values('status').annotate(count=Count('id'))
    collection_status_qs = HomeCollectionRequest.objects.values('status').annotate(count=Count('id'))

    # "Staff workload" — active home collections assigned per staff member, real data
    workload_qs = (
        HomeCollectionRequest.objects.filter(assigned_staff__isnull=False)
        .exclude(status__in=[HomeCollectionRequest.Status.COLLECTED, HomeCollectionRequest.Status.CANCELLED])
        .values('assigned_staff__username').annotate(count=Count('id')).order_by('-count')
    )

    context = {
        'today_appointments': today_appointments.count(),
        'pending_appointments': pending_appointments.count(),
        'samples_to_collect': samples_to_collect.count(),
        'processing_reports': processing_reports.count(),
        'reports_ready': reports_ready.count(),
        'home_collections': home_collections.count(),
        'recent_appointments': Appointment.objects.all().order_by('-created_at')[:8],

        'chart_daily_labels': json.dumps([d['day'].strftime('%d %b') for d in daily_qs if d['day']]),
        'chart_daily_data': json.dumps([d['count'] for d in daily_qs]),
        'chart_status_labels': json.dumps([dict(Appointment.Status.choices)[s['status']] for s in status_qs]),
        'chart_status_data': json.dumps([s['count'] for s in status_qs]),
        'chart_collection_status_labels': json.dumps([dict(HomeCollectionRequest.Status.choices)[c['status']] for c in collection_status_qs]),
        'chart_collection_status_data': json.dumps([c['count'] for c in collection_status_qs]),
        'chart_workload_labels': json.dumps([w['assigned_staff__username'] for w in workload_qs]),
        'chart_workload_data': json.dumps([w['count'] for w in workload_qs]),
    }
    return render(request, 'staff/dashboard.html', context)

@admin_required
def admin_dashboard_view(request):
    total_patients = User.objects.filter(role='PATIENT').count()
    total_staff = User.objects.filter(role='STAFF').count()
    total_appointments = Appointment.objects.count()
    total_revenue = Payment.objects.filter(status=Payment.Status.PAID).aggregate(total=Sum('amount'))['total'] or 0

    monthly_appts = (
        Appointment.objects.annotate(month=TruncMonth('created_at'))
        .values('month').annotate(count=Count('id')).order_by('month')
    )
    monthly_revenue = (
        Payment.objects.filter(status=Payment.Status.PAID)
        .annotate(month=TruncMonth('paid_at'))
        .values('month').annotate(total=Sum('amount')).order_by('month')
    )
    status_qs = Appointment.objects.values('status').annotate(count=Count('id'))
    payment_status_qs = Payment.objects.values('status').annotate(count=Count('id'))
    collection_status_qs = HomeCollectionRequest.objects.values('status').annotate(count=Count('id'))

    from tests_app.models import TestCategory, DiagnosticTest
    dept_qs = TestCategory.objects.annotate(count=Count('tests__appointments')).order_by('-count')[:8]
    top_tests_qs = DiagnosticTest.objects.annotate(count=Count('appointments')).order_by('-count')[:8]

    context = {
        'total_patients': total_patients,
        'total_staff': total_staff,
        'total_appointments': total_appointments,
        'total_revenue': total_revenue,
        'pending_appointments': Appointment.objects.filter(status=Appointment.Status.PENDING).count(),
        'pending_reports': Report.objects.filter(status=Report.Status.PENDING).count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'home_collection_count': HomeCollectionRequest.objects.exclude(
            status__in=[HomeCollectionRequest.Status.COLLECTED, HomeCollectionRequest.Status.CANCELLED]
        ).count(),
        'recent_users': User.objects.order_by('-created_at')[:6],

        'chart_appts_labels': json.dumps([m['month'].strftime('%b %Y') for m in monthly_appts]),
        'chart_appts_data': json.dumps([m['count'] for m in monthly_appts]),
        'chart_revenue_labels': json.dumps([m['month'].strftime('%b %Y') for m in monthly_revenue if m['month']]),
        'chart_revenue_data': json.dumps([float(m['total']) for m in monthly_revenue if m['month']]),
        'chart_status_labels': json.dumps([dict(Appointment.Status.choices)[s['status']] for s in status_qs]),
        'chart_status_data': json.dumps([s['count'] for s in status_qs]),
        'chart_dept_labels': json.dumps([d.name for d in dept_qs]),
        'chart_dept_data': json.dumps([d.count for d in dept_qs]),
        'chart_top_tests_labels': json.dumps([t.name for t in top_tests_qs]),
        'chart_top_tests_data': json.dumps([t.count for t in top_tests_qs]),
        'chart_payment_status_labels': json.dumps([dict(Payment.Status.choices)[p['status']] for p in payment_status_qs]),
        'chart_payment_status_data': json.dumps([p['count'] for p in payment_status_qs]),
        'chart_collection_status_labels': json.dumps([dict(HomeCollectionRequest.Status.choices)[c['status']] for c in collection_status_qs]),
        'chart_collection_status_data': json.dumps([c['count'] for c in collection_status_qs]),
    }
    return render(request, 'staff/admin_dashboard.html', context)

@admin_required
def admin_user_list_view(request):
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-created_at')

    if role_filter:
        users = users.filter(role=role_filter)

    context = {
        'users': users,
        'role_choices': User.Role.choices,
        'selected_role': role_filter,
    }
    return render(request, 'staff/admin_user_list.html', context)


@admin_required
def admin_user_detail_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        new_role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'

        valid_roles = [choice[0] for choice in User.Role.choices]

        # Guardrail: an admin should never be able to accidentally demote
        # or deactivate their OWN account through this form — that could
        # lock them out of the system with no other admin to fix it.
        if target_user == request.user:
            messages.error(request, "You cannot change your own role or active status here.")
            return redirect('admin_user_detail', user_id=target_user.id)

        if new_role in valid_roles:
            target_user.role = new_role
        target_user.is_active = is_active
        target_user.save()

        messages.success(request, f"Updated {target_user.username}.")
        return redirect('admin_user_detail', user_id=target_user.id)

    context = {'target_user': target_user, 'role_choices': User.Role.choices}
    return render(request, 'staff/admin_user_detail.html', context)