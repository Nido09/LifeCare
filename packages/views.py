from django.shortcuts import render, get_object_or_404
from .models import HealthPackage


def package_list_view(request):
    packages = HealthPackage.objects.filter(is_available=True)
    return render(request, 'packages/package_list.html', {'packages': packages})


def package_detail_view(request, package_code):
    package = get_object_or_404(HealthPackage, package_code=package_code)
    return render(request, 'packages/package_detail.html', {'package': package})