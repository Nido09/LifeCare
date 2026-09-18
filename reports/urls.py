from django.urls import path
from . import views

urlpatterns = [
    path('my-reports/', views.my_reports_view, name='my_reports'),

    path('staff/', views.staff_report_list_view, name='staff_report_list'),
    path('staff/choose/<str:appointment_id>/', views.staff_report_choice_view, name='staff_report_choice'),
    path('staff/create/<str:appointment_id>/', views.staff_report_create_view, name='staff_report_create'),
    path('staff/upload/<str:appointment_id>/', views.staff_report_upload_view, name='staff_report_upload'),
    path('staff/<uuid:report_uid>/', views.staff_report_detail_view, name='staff_report_detail'),

    path('<uuid:report_uid>/', views.report_detail_view, name='report_detail'),
    path('<uuid:report_uid>/download/', views.report_download_view, name='report_download'),
    path('<uuid:report_uid>/generate-pdf/', views.generate_report_pdf_view, name='generate_report_pdf'),
]