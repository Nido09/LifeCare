from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_dashboard_view, name='staff_dashboard'),

    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/users/', views.admin_user_list_view, name='admin_user_list'),
    path('admin/users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
]