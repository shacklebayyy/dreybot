from django.contrib import admin
from .models import DownloadToken

@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'order', 'product', 'download_count', 'max_downloads', 'expires_at', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('token', 'order__order_number', 'product__name')
