from django.shortcuts import render
from catalog.models import Category, Product

def landing_page(request):
    categories = Category.objects.filter(active=True)
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:6]
    return render(request, 'landing.html', {
        'categories': categories,
        'featured_products': featured_featured_products if 'featured_featured_products' in locals() else featured_products
    })
