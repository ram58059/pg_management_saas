from django.urls import path
from . import views

urlpatterns = [
    path('owner/properties/', views.properties_list, name='properties_list'),
    path('owner/properties/add/', views.property_create, name='property_create'),
    path('owner/properties/<int:pk>/edit/', views.property_update, name='property_update'),
    path('owner/properties/<int:pk>/delete/', views.property_delete, name='property_delete'),
    
    path('owner/rooms/', views.rooms_list, name='rooms_list'),
    path('owner/rooms/add/', views.room_create, name='room_create'),
    path('owner/rooms/<int:pk>/edit/', views.room_update, name='room_update'),
    path('owner/rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
]
