from django.urls import path
from . import views


urlpatterns = [
    path(
        'my-transactions/',
        views.my_transactions_view,
        name='my_transactions'
    ),
]