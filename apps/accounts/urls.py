from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('owner/login/', views.owner_login, name='owner_login'),
    path('tenant/login/', views.tenant_login, name='tenant_login'),
    path('logout/', views.logout_user, name='logout'),
]
