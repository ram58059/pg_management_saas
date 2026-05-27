from django.urls import path
from . import views

urlpatterns = [
    # Owner Routes
    # path('owner/invoices/', views.invoice_list, name='invoice_list'),
    # path('owner/invoices/generate/', views.generate_monthly_invoices, name='generate_monthly_invoices'),
    # path('owner/invoices/<int:invoice_id>/pay/', views.payment_create, name='payment_create'),
    path('owner/electricity-bills/', views.electricity_bills_manager, name='electricity_bills_manager'),
    path('owner/payment-settings/', views.payment_settings, name='payment_settings'),
    path('owner/payments/verify/', views.payment_verifications, name='payment_verifications'),
    path('owner/payments/<int:payment_id>/verify/', views.verify_payment, name='verify_payment'),
    
    # Shared Route
    path('receipt/<int:invoice_id>/', views.view_receipt, name='view_receipt'),
    
    # Tenant Routes
    path('tenant/payments/', views.tenant_payments, name='tenant_payments'),
    path('tenant/payments/<int:invoice_id>/download/', views.download_invoice, name='download_invoice'),
    path('tenant/payments/history/', views.tenant_payment_history, name='tenant_payment_history'),
    path('tenant/invoices/<int:invoice_id>/pay/', views.tenant_pay_rent, name='tenant_pay_rent'),
    path('tenant/payments/create-intent/', views.tenant_payment_intent, name='tenant_payment_intent'),
    path('tenant/payments/<int:payment_id>/pay/', views.tenant_payment_page, name='tenant_payment_page'),
]
