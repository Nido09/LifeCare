from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = [
        'payment_id',
        'appointment',
        'amount',
        'payment_method',
        'status',
        'created_at',
        'paid_at'
    ]

    list_filter = ['status', 'payment_method']

    search_fields = ['payment_id']

    readonly_fields = [
        'payment_id',
        'created_at',
        'paid_at'
    ]