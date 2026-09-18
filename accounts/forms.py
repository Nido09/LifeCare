from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import User

GENDER_CHOICES = [
    ('', 'Select...'),
    ('MALE', 'Male'),
    ('FEMALE', 'Female'),
    ('OTHER', 'Other'),
    ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
]

# Area -> district. Only these areas are eligible for registration/booking.
MUMBAI_AREAS = {
    'Dadar': 'Mumbai City', 'Mahim': 'Mumbai City', 'Matunga': 'Mumbai City',
    'Sion': 'Mumbai City', 'Wadala': 'Mumbai City', 'Worli': 'Mumbai City',
    'Prabhadevi': 'Mumbai City', 'Lower Parel': 'Mumbai City', 'Parel': 'Mumbai City',
    'Colaba': 'Mumbai City', 'Fort': 'Mumbai City', 'Churchgate': 'Mumbai City',
    'Byculla': 'Mumbai City',
    'Bandra': 'Mumbai Suburban', 'Khar': 'Mumbai Suburban', 'Santacruz': 'Mumbai Suburban',
    'Vile Parle': 'Mumbai Suburban', 'Andheri': 'Mumbai Suburban', 'Jogeshwari': 'Mumbai Suburban',
    'Goregaon': 'Mumbai Suburban', 'Malad': 'Mumbai Suburban', 'Kandivali': 'Mumbai Suburban',
    'Borivali': 'Mumbai Suburban', 'Dahisar': 'Mumbai Suburban', 'Kurla': 'Mumbai Suburban',
    'Ghatkopar': 'Mumbai Suburban', 'Vikhroli': 'Mumbai Suburban', 'Kanjurmarg': 'Mumbai Suburban',
    'Bhandup': 'Mumbai Suburban', 'Mulund': 'Mumbai Suburban', 'Chembur': 'Mumbai Suburban',
    'Powai': 'Mumbai Suburban', 'Trombay': 'Mumbai Suburban',
}

MUMBAI_AREA_CHOICES = [('', 'Select your area...')] + [(a, a) for a in sorted(MUMBAI_AREAS.keys())]

UNSUPPORTED_LOCATION_MESSAGE = (
    "Sorry, LifeCare Diagnostic Center currently provides services only within Mumbai."
)


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    phone_number = forms.CharField(max_length=15, required=True)
    mumbai_area = forms.ChoiceField(choices=MUMBAI_AREA_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.now().date():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_mumbai_area(self):
        # Server-side gate — the real enforcement. Never trust that only
        # the dropdown's own options could have been submitted; a modified
        # POST request could contain anything.
        area = self.cleaned_data.get('mumbai_area', '').strip()
        if area not in MUMBAI_AREAS:
            raise forms.ValidationError(UNSUPPORTED_LOCATION_MESSAGE)
        return area

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone_number', '')
        digits_only = phone.replace(' ', '')

        if digits_only and not digits_only.isdigit():
            self.add_error('phone_number', "Phone number must contain digits only.")
        elif len(digits_only) != 10:
            self.add_error('phone_number', "Please enter exactly 10 digits.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PATIENT
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.country_code = '+91'
        if commit:
            user.save()
        return user