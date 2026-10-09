from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import landing_page, ping_health_check

urlpatterns = [
    path('', landing_page, name='landing'),
    path('ping/', ping_health_check, name='ping_health'),
    path('admin-panel/', include('dashboard.urls', namespace='dashboard')),
    path('admin/', admin.site.urls),
    path('download/', include('downloads.urls', namespace='downloads')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
