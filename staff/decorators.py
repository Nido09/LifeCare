from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_or_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role not in ['STAFF', 'ADMIN']:
            messages.error(request, "That page is only available to staff accounts.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'ADMIN':
            messages.error(request, "That page is only available to admin accounts.")
            return redirect('dashboard_redirect')
        return view_func(request, *args, **kwargs)
    return wrapper