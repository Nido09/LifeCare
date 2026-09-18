from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from staff.decorators import staff_or_admin_required
from accounts.models import User
from .models import HomeCollectionRequest


@staff_or_admin_required
def staff_collection_list_view(request):
    status_filter = request.GET.get('status', '')
    requests_qs = HomeCollectionRequest.objects.all()

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    context = {
        'requests': requests_qs,
        'status_choices': HomeCollectionRequest.Status.choices,
        'selected_status': status_filter,
    }
    return render(request, 'samples/staff_collection_list.html', context)


@staff_or_admin_required
def staff_collection_detail_view(request, request_id):
    collection_request = get_object_or_404(HomeCollectionRequest, request_id=request_id)
    staff_users = User.objects.filter(role='STAFF')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        assigned_staff_id = request.POST.get('assigned_staff')
        staff_notes = request.POST.get('staff_notes', '').strip()

        valid_statuses = [choice[0] for choice in HomeCollectionRequest.Status.choices]
        if new_status in valid_statuses:
            collection_request.status = new_status

        if assigned_staff_id:
            collection_request.assigned_staff_id = assigned_staff_id
        else:
            collection_request.assigned_staff = None

        collection_request.staff_notes = staff_notes

        if new_status == HomeCollectionRequest.Status.COLLECTED and not collection_request.collected_at:
            collection_request.collected_at = timezone.now()

        collection_request.save()
        messages.success(request, "Collection request updated.")
        return redirect('staff_collection_detail', request_id=collection_request.request_id)

    context = {
        'collection_request': collection_request,
        'staff_users': staff_users,
        'status_choices': HomeCollectionRequest.Status.choices,
    }
    return render(request, 'samples/staff_collection_detail.html', context)