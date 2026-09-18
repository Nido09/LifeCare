from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_list_view, name='test_list'),
    path('<str:test_code>/', views.test_detail_view, name='test_detail'),
]