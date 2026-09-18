from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ContactMessage, HomeCollectionInquiry
from .models import Feedback

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role', 'phone_number')}),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'email', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject']


@admin.register(HomeCollectionInquiry)
class HomeCollectionInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'preferred_date', 'is_contacted', 'created_at']
    list_filter = ['is_contacted']
    

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'rating', 'status', 'created_at']
    list_filter = ['status', 'rating']
    list_editable = ['status']
    search_fields = ['guest_name', 'guest_email', 'user__username']