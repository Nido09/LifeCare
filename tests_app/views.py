from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import DiagnosticTest, TestCategory


def test_list_view(request):
    tests = DiagnosticTest.objects.filter(is_available=True).select_related('category')
    categories = TestCategory.objects.all()

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    if query:
        tests = tests.filter(Q(name__icontains=query) | Q(test_code__icontains=query))
    if category_slug:
        tests = tests.filter(category__slug=category_slug)

    tests = tests.order_by('category__name', 'name')

    # Group tests under their department for the accordion layout.
    # Only departments with at least one matching test are shown.
    grouped = {}
    for t in tests:
        grouped.setdefault(t.category, []).append(t)
    departments = [{'category': cat, 'tests': items} for cat, items in grouped.items()]

    from appointments.views import _cart_test_ids

    context = {
        'departments': departments,
        'categories': categories,
        'query': query,
        'selected_category': category_slug,
        'cart_test_ids': _cart_test_ids(request),
        'total_test_count': tests.count(),
    }
    return render(request, 'tests_app/test_list.html', context)


def test_detail_view(request, test_code):
    test = get_object_or_404(DiagnosticTest, test_code=test_code)
    related_tests = DiagnosticTest.objects.filter(category=test.category).exclude(id=test.id)[:4]
    context = {'test': test, 'related_tests': related_tests}
    return render(request, 'tests_app/test_detail.html', context)