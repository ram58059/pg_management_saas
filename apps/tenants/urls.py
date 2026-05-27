from django.urls import path
from . import views

urlpatterns = [
    path('owner/tenants/', views.tenants_list, name='tenants_list'),
    path('owner/tenants/add/', views.tenant_create, name='tenant_create'),
    path('owner/tenants/<int:pk>/shift/', views.tenant_shift, name='tenant_shift'),
    path('owner/tenants/<int:pk>/dues/', views.api_tenant_dues_list, name='api_tenant_dues_list'),
    path('owner/tenants/<int:pk>/dues/save/', views.api_tenant_due_save, name='api_tenant_due_save'),
    path('owner/tenants/<int:pk>/dues/<int:due_id>/delete/', views.api_tenant_due_delete, name='api_tenant_due_delete'),
    path('ajax/load-rooms/', views.load_rooms, name='ajax_load_rooms'),
    path('owner/tenants/<int:pk>/details/', views.api_tenant_details, name='api_tenant_details'),
    path('owner/tenants/<int:pk>/update/', views.api_tenant_update, name='api_tenant_update'),
    path('owner/tenants/<int:pk>/delete/', views.api_tenant_delete, name='api_tenant_delete'),
]
