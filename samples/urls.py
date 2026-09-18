from django.urls import path
from . import views

urlpatterns = [
    path('staff/', views.staff_collection_list_view, name='staff_collection_list'),
    path('staff/<str:request_id>/', views.staff_collection_detail_view, name='staff_collection_detail'),
]