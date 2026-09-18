from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('profile/', views.patient_profile_view, name='patient_profile'),
]