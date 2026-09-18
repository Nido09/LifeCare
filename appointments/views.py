from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings
from tests_app.models import DiagnosticTest
from packages.models import HealthPackage
from patients.models import PatientProfile
from notifications.utils import notify
from notifications.models import Notification
from .models import Appointment
from functools import wraps

def staff_or_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role not in ['STAFF', 'ADMIN']:
            messages.error(request, "That page is only available to staff accounts.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_cart(request):
    return request.session.setdefault('booking_cart', [])


def _cart_test_ids(request):
    cart = _get_cart(request)
    return {c['id'] for c in cart if c['type'] == 'test'}


def add_to_cart_view(request, item_type, item_id):
    if request.user.is_authenticated and request.user.role not in ['PATIENT']:
        messages.error(request, "Only patient accounts can book tests.")
        return redirect('dashboard_redirect')

    if item_type == 'test':
        get_object_or_404(DiagnosticTest, id=item_id, is_available=True)
    elif item_type == 'package':
        get_object_or_404(HealthPackage, id=item_id, is_available=True)
    else:
        messages.error(request, "Invalid item.")
        return redirect('home')

    cart = _get_cart(request)
    entry = {'type': item_type, 'id': item_id}
    if entry not in cart:
        cart.append(entry)
        request.session.modified = True
        messages.success(request, "Added to your booking cart.")
    else:
        messages.info(request, "That's already in your cart.")

    return redirect(request.META.get('HTTP_REFERER', '/'))


def add_multiple_to_cart_view(request):
    if request.method != 'POST':
        return redirect('test_list')

    test_ids = request.POST.getlist('test_ids')
    if not test_ids:
        messages.error(request, "Please select at least one test.")
        return redirect('test_list')

    valid_tests = DiagnosticTest.objects.filter(id__in=test_ids, is_available=True)
    valid_ids = set(valid_tests.values_list('id', flat=True))

    if not valid_ids:
        messages.error(request, "None of the selected tests are currently available.")
        return redirect('test_list')

    cart = _get_cart(request)
    added_count = 0
    for test_id in valid_ids:
        entry = {'type': 'test', 'id': test_id}
        if entry not in cart:
            cart.append(entry)
            added_count += 1

    request.session.modified = True

    skipped = len(test_ids) - len(valid_ids)
    if skipped:
        messages.info(request, f"{skipped} selected test(s) were unavailable and skipped.")
    messages.success(request, f"{added_count} test(s) added to your cart.")

    return redirect('booking_cart')


def remove_from_cart_view(request, item_type, item_id):
    cart = _get_cart(request)
    entry = {'type': item_type, 'id': item_id}
    if entry in cart:
        cart.remove(entry)
        request.session.modified = True
        messages.info(request, "Removed from cart.")
    return redirect('booking_cart')


def booking_cart_view(request):
    cart = _get_cart(request)
    test_ids = [c['id'] for c in cart if c['type'] == 'test']
    package_ids = [c['id'] for c in cart if c['type'] == 'package']

    tests = DiagnosticTest.objects.filter(id__in=test_ids, is_available=True)
    packages = HealthPackage.objects.filter(id__in=package_ids, is_available=True)

    total = (tests.aggregate(t=Sum('price'))['t'] or 0) + (packages.aggregate(t=Sum('price'))['t'] or 0)

    context = {'tests': tests, 'packages': packages, 'total': total}
    return render(request, 'appointments/cart.html', context)


def _send_booking_confirmation_email(request, appointment, tests, packages):
    """
    Sent once, right after a booking is created. fail_silently=True is
    deliberate: if SMTP isn't configured yet, a booking must NEVER be
    blocked or rolled back just because the confirmation email couldn't
    be delivered — the appointment itself is already safely saved.
    """
    if not request.user.email:
        return

    item_lines = [f"- {t.name} (₹{t.price})" for t in tests]
    item_lines += [f"- {p.name} [Package] (₹{p.price})" for p in packages]

    message = (
        f"Dear {request.user.get_full_name() or request.user.username},\n\n"
        f"Your LifeCare Diagnostic Center appointment has been booked successfully.\n\n"
        f"Appointment ID: {appointment.appointment_id}\n"
        f"Date & Time: {appointment.preferred_date} at {appointment.preferred_time}\n"
        f"Collection: {appointment.get_collection_type_display()}\n\n"
        f"Tests booked:\n" + "\n".join(item_lines) + "\n\n"
        f"Amount Due: ₹{appointment.total_amount}\n\n"
        f"Please make the payment at the laboratory during your visit.\n\n"
        f"— LIFE CARE DIAGNOSTIC CENTER"
    )

    send_mail(
        subject=f"LifeCare Appointment Confirmed — {appointment.appointment_id}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=True,
    )


@login_required
def checkout_view(request):
    if request.user.role != 'PATIENT':
        messages.error(request, "Only patient accounts can book appointments.")
        return redirect('dashboard_redirect')

    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Your booking cart is empty. Add a test or package first.")
        return redirect('test_list')

    test_ids = [c['id'] for c in cart if c['type'] == 'test']
    package_ids = [c['id'] for c in cart if c['type'] == 'package']
    tests = DiagnosticTest.objects.filter(id__in=test_ids, is_available=True)
    packages = HealthPackage.objects.filter(id__in=package_ids, is_available=True)

    if not tests.exists() and not packages.exists():
        messages.error(request, "The items in your cart are no longer available.")
        return redirect('booking_cart')

    total = (tests.aggregate(t=Sum('price'))['t'] or 0) + (packages.aggregate(t=Sum('price'))['t'] or 0)

    if request.method == 'POST':
        preferred_date = request.POST.get('preferred_date')
        preferred_time = request.POST.get('preferred_time')
        collection_type = request.POST.get('collection_type')
        address = request.POST.get('address', '').strip()
        notes = request.POST.get('notes', '').strip()

        # Online payment is not offered to patients. Regardless of what
        # a request might contain, every booking is always Pay-at-Lab —
        # enforced here server-side, not just by hiding a UI option.
        payment_preference = Appointment.PaymentPreference.PAY_AT_LAB

        if not preferred_date or not preferred_time or not collection_type:
            messages.error(request, "Please fill in date, time, and collection type.")
            return render(request, 'appointments/checkout.html', {'tests': tests, 'packages': packages, 'total': total})

        if collection_type == Appointment.CollectionType.HOME_COLLECTION and not address:
            messages.error(request, "Address is required for home collection.")
            return render(request, 'appointments/checkout.html', {'tests': tests, 'packages': packages, 'total': total})

        profile, _ = PatientProfile.objects.get_or_create(user=request.user)

        appointment = Appointment.objects.create(
            patient=profile,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            collection_type=collection_type,
            payment_preference=payment_preference,
            address=address,
            notes=notes,
            total_amount=total,
        )

        appointment.tests.set(tests)
        appointment.packages.set(packages)

        notify(
            recipient=request.user,
            title="Appointment Booked",
            message=f"Your appointment {appointment.appointment_id} has been booked for {preferred_date} at {preferred_time}. Payment will be made at the laboratory.",
            notification_type=Notification.NotificationType.APPOINTMENT,
            link_url=f"/appointments/{appointment.appointment_id}/",
        )

        _send_booking_confirmation_email(request, appointment, tests, packages)

        if collection_type == Appointment.CollectionType.HOME_COLLECTION:
            from samples.models import HomeCollectionRequest
            HomeCollectionRequest.objects.create(
                appointment=appointment,
                contact_number=request.user.phone_number or '',
                address=address,
                scheduled_date=preferred_date,
                scheduled_time=preferred_time,
            )

        request.session['booking_cart'] = []
        request.session.modified = True

        messages.success(
            request,
            f"Your appointment {appointment.appointment_id} has been booked successfully. "
            f"Payment will be made at the laboratory."
        )
        return redirect('appointment_detail', appointment_id=appointment.appointment_id)

    return render(request, 'appointments/checkout.html', {'tests': tests, 'packages': packages, 'total': total})


@login_required
def my_appointments_view(request):
    if request.user.role != 'PATIENT':
        return redirect('dashboard_redirect')

    profile, _ = PatientProfile.objects.get_or_create(user=request.user)
    appointments = Appointment.objects.filter(patient=profile)
    return render(request, 'appointments/my_appointments.html', {'appointments': appointments})


@login_required
def appointment_detail_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    if request.user.role == 'PATIENT' and appointment.patient.user != request.user:
        messages.error(request, "You don't have permission to view that appointment.")
        return redirect('my_appointments')

    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})


@login_required
def cancel_appointment_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    if appointment.patient.user != request.user:
        messages.error(request, "You don't have permission to cancel that appointment.")
        return redirect('my_appointments')

    if appointment.status in [Appointment.Status.PENDING, Appointment.Status.CONFIRMED]:
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()

        notify(
            recipient=request.user,
            title="Appointment Cancelled",
            message=f"Your appointment {appointment.appointment_id} has been cancelled.",
            notification_type=Notification.NotificationType.STATUS_CHANGE,
            link_url=f"/appointments/{appointment.appointment_id}/",
        )
        messages.success(request, "Appointment cancelled.")
    else:
        messages.error(request, "This appointment can no longer be cancelled — it's already in progress.")

    return redirect('my_appointments')


# =========================================================
# STAFF VIEWS
# =========================================================

@staff_or_admin_required
def staff_appointment_list_view(request):
    status_filter = request.GET.get('status', '')
    appointments = Appointment.objects.all()

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    context = {
        'appointments': appointments,
        'status_choices': Appointment.Status.choices,
        'selected_status': status_filter,
    }
    return render(request, 'appointments/staff_appointment_list.html', context)


@staff_or_admin_required
def staff_appointment_detail_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [choice[0] for choice in Appointment.Status.choices]

        if new_status in valid_statuses:
            old_status = appointment.status
            appointment.status = new_status
            appointment.save()

            if old_status != new_status:
                notify(
                    recipient=appointment.patient.user,
                    title="Appointment Status Updated",
                    message=f"Your appointment {appointment.appointment_id} is now: {appointment.get_status_display()}.",
                    notification_type=Notification.NotificationType.STATUS_CHANGE,
                    link_url=f"/appointments/{appointment.appointment_id}/",
                )
            messages.success(request, f"Status updated to {appointment.get_status_display()}.")
        else:
            messages.error(request, "Invalid status.")

        return redirect('staff_appointment_detail', appointment_id=appointment.appointment_id)

    context = {
        'appointment': appointment,
        'status_choices': Appointment.Status.choices,
    }
    return render(request, 'appointments/staff_appointment_detail.html', context)


@staff_or_admin_required
def staff_mark_paid_at_lab_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    already_paid = appointment.payments.filter(status='PAID').exists()
    if already_paid:
        messages.info(request, "This appointment is already marked as paid.")
        return redirect('staff_appointment_detail', appointment_id=appointment.appointment_id)

    from payments.models import Payment
    from django.utils import timezone

    payment = Payment.objects.create(
        appointment=appointment,
        amount=appointment.total_amount,
        payment_method=Payment.Method.PAY_AT_LAB,
        status=Payment.Status.PAID,
        paid_at=timezone.now(),
    )

    # Payment confirmation email — only reached on genuine, first-time
    # marking as PAID (the already_paid check above guarantees this
    # can't fire twice for the same appointment).
    patient_user = appointment.patient.user
    if patient_user.email:
        message = (
            f"Dear {patient_user.get_full_name() or patient_user.username},\n\n"
            f"We have received your payment at LIFE CARE DIAGNOSTIC CENTER.\n\n"
            f"Payment ID: {payment.payment_id}\n"
            f"Appointment ID: {appointment.appointment_id}\n"
            f"Amount Paid: ₹{payment.amount}\n"
            f"Date: {payment.paid_at.strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"Thank you for choosing LifeCare.\n\n"
            f"— LIFE CARE DIAGNOSTIC CENTER"
        )
        send_mail(
            subject=f"LifeCare Payment Received — {payment.payment_id}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[patient_user.email],
            fail_silently=True,
        )

    notify(
        recipient=patient_user,
        title="Payment Received",
        message=f"We've received your payment of ₹{payment.amount} for {appointment.appointment_id}.",
        notification_type=Notification.NotificationType.PAYMENT,
        link_url=f"/appointments/{appointment.appointment_id}/",
    )

    messages.success(request, f"Payment of ₹{appointment.total_amount} recorded as collected at lab.")
    return redirect('staff_appointment_detail', appointment_id=appointment.appointment_id)