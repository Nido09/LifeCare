from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import PatientRegistrationForm
from patients.models import PatientProfile
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            area = form.cleaned_data['mumbai_area']
            from accounts.forms import MUMBAI_AREAS
            district = MUMBAI_AREAS[area]

            PatientProfile.objects.create(
                user=user,
                date_of_birth=form.cleaned_data['date_of_birth'],
                gender=form.cleaned_data['gender'],
                area=area,
                city='Mumbai',
                district=district,
                state='Maharashtra',
                country='India',
            )
            login(request, user)
            messages.success(request, 'Welcome to LIFE CARE DIAGNOSTIC CENTER! Your account has been created.')
            return redirect('dashboard_redirect')
        else:
            # If the only failure was the Mumbai check, surface that exact
            # message even more prominently than the generic field error.
            if 'mumbai_area' in form.errors:
                messages.error(request, form.errors['mumbai_area'][0])
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

class RoleBasedLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        # Respect Django's built-in ?next=... redirect (e.g. sent here from
        # checkout when an anonymous user tries to book). Falls back to the
        # normal role-based dashboard if no safe "next" was provided.
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        return reverse_lazy('dashboard_redirect')


def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')

    role = request.user.role
    if role == 'ADMIN':
        return redirect('admin_dashboard')
    elif role == 'STAFF':
        return redirect('staff_dashboard')
    else:
        return redirect('patient_dashboard')

from django.contrib.auth.decorators import login_required


@login_required
def patient_dashboard_placeholder(request):
    return render(request, 'accounts/placeholder_dashboard.html', {'role': 'Patient'})


@login_required
def staff_dashboard_placeholder(request):
    if request.user.role not in ['STAFF', 'ADMIN']:
        return redirect('dashboard_redirect')
    return render(request, 'accounts/placeholder_dashboard.html', {'role': 'Staff'})


@login_required
def admin_dashboard_placeholder(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard_redirect')
    return render(request, 'accounts/placeholder_dashboard.html', {'role': 'Admin'})