from django.contrib import admin
from .models import Category, Country, Region, Product, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'active', 'ordering')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code', 'flag_emoji', 'active')
    search_fields = ('name', 'iso_code')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'code', 'active')
    list_filter = ('country', 'active')
    search_fields = ('name', 'code')

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'country', 'state', 'price', 'file_type', 'is_active', 'stock_status')
    list_filter = ('category', 'country', 'is_active', 'stock_status')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
