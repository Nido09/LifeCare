from django.contrib import admin
from .models import TestCategory, DiagnosticTest


@admin.register(TestCategory)
class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DiagnosticTest)
class DiagnosticTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'test_code', 'category', 'price', 'is_fasting_required', 'is_available']
    list_filter = ['category', 'is_fasting_required', 'is_available']
    search_fields = ['name', 'test_code']
    list_editable = ['is_fasting_required', 'is_available']
    fieldsets = (
        (None, {'fields': ('name', 'test_code', 'category', 'price', 'is_available')}),
        ('Patient Information', {'fields': ('description', 'sample_type', 'turnaround_time_hours')}),
        ('Preparation & Fasting', {'fields': ('preparation_instructions', 'is_fasting_required', 'fasting_instructions')}),
    )