from django.urls import path
from . import views

urlpatterns = [
    path('', views.package_list_view, name='package_list'),
    path('<str:package_code>/', views.package_detail_view, name='package_detail'),
]