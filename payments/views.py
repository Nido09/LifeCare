from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from .models import Payment


@login_required
def my_transactions_view(request):
    if request.user.role != 'PATIENT':
        return redirect('dashboard_redirect')

    transactions = Payment.objects.filter(
        appointment__patient__user=request.user
    ).select_related('appointment').order_by('-created_at')

    total_paid = transactions.filter(status=Payment.Status.PAID).aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, 'payments/my_transactions.html', {
        'transactions': transactions,
        'total_paid': total_paid,
    })