from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient', 'preferred_date', 'collection_type', 'status', 'total_amount']
    list_filter = ['status', 'collection_type']
    search_fields = ['appointment_id', 'patient__patient_id']