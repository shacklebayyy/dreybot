from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import landing_page

urlpatterns = [
    path('', landing_page, name='landing'),
    path('admin-panel/', include('dashboard.urls', namespace='dashboard')),
    path('admin/', admin.site.urls),
    path('download/', include('downloads.urls', namespace='downloads')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
