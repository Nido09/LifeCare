from django.contrib import admin
from .models import HomeCollectionRequest


@admin.register(HomeCollectionRequest)
class HomeCollectionRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_id', 'appointment', 'status', 'assigned_staff',
        'scheduled_date', 'scheduled_time', 'collected_at'
    ]
    list_filter = ['status', 'scheduled_date']
    search_fields = ['request_id', 'appointment__appointment_id', 'contact_number']
    list_editable = ['status', 'assigned_staff']
    autocomplete_fields = ['assigned_staff']