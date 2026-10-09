from django.shortcuts import render
from django.http import HttpResponse
from catalog.models import Category, Product

def landing_page(request):
    try:
        categories = list(Category.objects.filter(active=True))
        featured_products = list(Product.objects.filter(is_active=True, is_featured=True)[:6])
    except Exception:
        categories = []
        featured_products = []
    return render(request, 'landing.html', {
        'categories': categories,
        'featured_products': featured_products
    })

def ping_health_check(request):
    return HttpResponse("OK - DreyDocs Active", content_type="text/plain", status=200)
