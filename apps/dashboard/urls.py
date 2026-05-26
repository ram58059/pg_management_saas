from django.urls import path
from . import views

urlpatterns = [
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
]
