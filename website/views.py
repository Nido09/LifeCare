from django.shortcuts import render, redirect
from django.contrib import messages
from tests_app.models import DiagnosticTest, TestCategory
from packages.models import HealthPackage
from accounts.models import ContactMessage, HomeCollectionInquiry
from accounts.models import Feedback

def home_view(request):
    popular_tests = DiagnosticTest.objects.filter(is_available=True).order_by('id')[:6]
    categories = TestCategory.objects.all()[:8]
    packages = HealthPackage.objects.filter(is_available=True)[:3]

    context = {
        'popular_tests': popular_tests,
        'categories': categories,
        'packages': packages,
        'total_tests': DiagnosticTest.objects.filter(is_available=True).count(),
        'total_categories': TestCategory.objects.count(),
        'total_packages': HealthPackage.objects.filter(is_available=True).count(),
    }

    # Pre-fill home collection form for logged-in patients from their real
    # profile data — never invented, only what they already gave us.
    if request.user.is_authenticated and request.user.role == 'PATIENT':
        from patients.models import PatientProfile
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        context['prefill_name'] = request.user.get_full_name() or request.user.username
        context['prefill_phone'] = request.user.phone_number
        context['prefill_address'] = profile.address

    return render(request, 'website/home.html', context)

def about_view(request):
    return render(request, 'website/about.html')


def faq_view(request):
    return render(request, 'website/faq.html')


def contact_view(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            name = request.user.get_full_name() or request.user.username
            email = request.user.email
        else:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()

        phone = request.POST.get('phone_number', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and subject and message:
            ContactMessage.objects.create(
                name=name, email=email, phone_number=phone,
                subject=subject, message=message
            )
            messages.success(request, "Thanks! We've received your message and will get back to you soon.")
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'website/contact.html')


def home_collection_inquiry_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        preferred_date = request.POST.get('preferred_date') or None
        notes = request.POST.get('notes', '').strip()

        if name and phone and address:
            HomeCollectionInquiry.objects.create(
                name=name, phone_number=phone, address=address,
                preferred_date=preferred_date, notes=notes
            )
            messages.success(request, "Request received! Our team will call you shortly to confirm.")
            return redirect('home')
        else:
            messages.error(request, "Please fill in your name, phone number, and address.")
            return redirect('home')

    return redirect('home')

def feedback_view(request):
    # Logged-in patients: never re-ask for name/email — pulled straight
    # from their existing account. Only prompt for a name if one is
    # genuinely missing on file (nothing invented, nothing duplicated).
    needs_name = False
    if request.user.is_authenticated:
        needs_name = not request.user.get_full_name().strip()

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        if not rating or not comment:
            messages.error(request, "Please provide a rating and your feedback.")
            return render(request, 'website/feedback.html', {'needs_name': needs_name})

        if request.user.is_authenticated:
            if needs_name:
                name = request.POST.get('name', '').strip()
                if name:
                    # Update the account itself with the name they gave —
                    # single source of truth, not a separate copy.
                    parts = name.split(' ', 1)
                    request.user.first_name = parts[0]
                    request.user.last_name = parts[1] if len(parts) > 1 else ''
                    request.user.save()
            Feedback.objects.create(user=request.user, rating=rating, comment=comment)
        else:
            guest_name = request.POST.get('guest_name', '').strip()
            guest_email = request.POST.get('guest_email', '').strip()
            if not guest_name or not guest_email:
                messages.error(request, "Please provide your name and email.")
                return render(request, 'website/feedback.html', {'needs_name': needs_name})
            Feedback.objects.create(guest_name=guest_name, guest_email=guest_email, rating=rating, comment=comment)

        messages.success(request, "Thank you! Your feedback has been submitted and will appear after review.")
        return redirect('home')

    return render(request, 'website/feedback.html', {'needs_name': needs_name})