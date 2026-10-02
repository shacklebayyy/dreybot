from django.urls import path
from .views import download_file_view

app_name = 'downloads'

urlpatterns = [
    path('<str:token_str>/', download_file_view, name='secure_download'),
]
