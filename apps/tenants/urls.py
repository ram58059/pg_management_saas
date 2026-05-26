from django.urls import path
from . import views

urlpatterns = [
    path('owner/tenants/', views.tenants_list, name='tenants_list'),
    path('owner/tenants/add/', views.tenant_create, name='tenant_create'),
    path('owner/tenants/<int:pk>/shift/', views.tenant_shift, name='tenant_shift'),
    path('ajax/load-rooms/', views.load_rooms, name='ajax_load_rooms'),
]
