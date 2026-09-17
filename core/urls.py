from django.urls import path
from django.contrib.auth.views import LogoutView
from core.views import tenant, admin
from core.views.accueil import accueil

urlpatterns = [
    path('', accueil, name='accueil'),
    path('login/', accueil, name='login'),
    path('register/', accueil, name='register'),
    path('demo/', accueil, name='demo_login'),
    path('logout/', LogoutView.as_view(next_page='accueil'), name='logout'),

    path('dashboard/', tenant.dashboard, name='dashboard'),
    path('tenant/dashboard/', tenant.dashboard, name='tenant_dashboard'),

    path('clients/', tenant.clients_list, name='clients_list'),
    path('clients/add/', tenant.client_add, name='client_add'),
    path('clients/<int:pk>/edit/', tenant.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', tenant.client_delete, name='client_delete'),

    path('products/', tenant.products_list, name='products_list'),
    path('products/add/', tenant.product_add, name='product_add'),
    path('products/<int:pk>/edit/', tenant.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', tenant.product_delete, name='product_delete'),

    path('services/', tenant.services_list, name='services_list'),
    path('services/add/', tenant.service_add, name='service_add'),
    path('services/<int:pk>/edit/', tenant.service_edit, name='service_edit'),
    path('services/<int:pk>/delete/', tenant.service_delete, name='service_delete'),

    path('quotes/', tenant.quotes_list, name='quotes_list'),
    path('quotes/add/', tenant.quote_add, name='quote_add'),
    path('quotes/<int:pk>/', tenant.quote_detail, name='quote_detail'),
    path('quotes/<int:pk>/pdf/', tenant.quote_pdf, name='quote_pdf'),
    path('quotes/<int:pk>/delete/', tenant.quote_delete, name='quote_delete'),
    path('quotes/<int:pk>/to-invoice/', tenant.quote_to_invoice, name='quote_to_invoice'),

    path('invoices/', tenant.invoices_list, name='invoices_list'),
    path('invoices/add/', tenant.invoice_add, name='invoice_add'),
    path('invoices/<int:pk>/', tenant.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/pdf/', tenant.invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/delete/', tenant.invoice_delete, name='invoice_delete'),

    path('tenant/settings/', tenant.settings_view, name='settings'),

    path('sysadmin/', admin.admin_dashboard, name='admin_dashboard'),
    path('sysadmin/companies/', admin.admin_companies, name='admin_companies'),
    path('sysadmin/companies/<int:pk>/', admin.admin_company_detail, name='admin_company_detail'),
    path('sysadmin/users/', admin.admin_users, name='admin_users'),
    path('sysadmin/settings/', admin.admin_settings, name='admin_settings'),
]