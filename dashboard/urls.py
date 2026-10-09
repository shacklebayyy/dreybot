from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('categories/', views.category_list, name='category_list'),
    path('countries/', views.country_list, name='country_list'),
    path('states/', views.state_list, name='state_list'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('verification/', views.verification_list, name='verification_list'),
    path('verification/<int:req_id>/', views.verification_detail, name='verification_detail'),
    path('verification/providers/', views.provider_list, name='provider_list'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('topups/', views.topup_request_list, name='topup_request_list'),
    path('audit/', views.audit_list, name='audit_list'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/payments/', views.payment_settings_view, name='payment_settings'),
]


