from django.contrib import admin
from .models import Report, ReportResult


class ReportResultInline(admin.TabularInline):
    model = ReportResult
    extra = 0
    fields = ['test', 'result_value', 'reference_range', 'units', 'abnormal_flag']
    autocomplete_fields = ['test']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['report_uid', 'appointment', 'patient', 'origin', 'status', 'is_demo_data', 'created_at']
    list_filter = ['origin', 'status', 'is_demo_data']
    search_fields = ['patient__patient_id', 'appointment__appointment_id']
    readonly_fields = ['report_uid']
    inlines = [ReportResultInline]