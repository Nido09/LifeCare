from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.booking_cart_view, name='booking_cart'),
    path('cart/add/<str:item_type>/<int:item_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/add-multiple/', views.add_multiple_to_cart_view, name='add_multiple_to_cart'),
    path('cart/remove/<str:item_type>/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('my-appointments/', views.my_appointments_view, name='my_appointments'),

    path('staff/', views.staff_appointment_list_view, name='staff_appointment_list'),
    path('staff/<str:appointment_id>/', views.staff_appointment_detail_view, name='staff_appointment_detail'),
    path('staff/<str:appointment_id>/mark-paid/', views.staff_mark_paid_at_lab_view, name='staff_mark_paid_at_lab'),

    path('<str:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('<str:appointment_id>/cancel/', views.cancel_appointment_view, name='cancel_appointment'),
]