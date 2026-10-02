from django.shortcuts import render
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
