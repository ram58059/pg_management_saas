from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from apps.accounts.models import CustomUser
from apps.properties.models import Property, Room
from .models import Tenant
from .forms import TenantUserForm, TenantProfileForm
from django.http import JsonResponse

@login_required
def tenants_list(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    tenants = Tenant.objects.filter(pg_property__owner=request.user.pg_owner_profile).select_related('user', 'room', 'pg_property')
    return render(request, 'owner/tenants.html', {'tenants': tenants})

@login_required
def tenant_create(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    if request.method == 'POST':
        user_form = TenantUserForm(request.POST)
        profile_form = TenantProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.role = CustomUser.Role.TENANT
                user.save()
                
                tenant = profile_form.save(commit=False)
                tenant.user = user
                tenant.save()
                
            messages.success(request, f"Tenant {user.get_full_name()} onboarded successfully.")
            return redirect('tenants_list')
    else:
        user_form = TenantUserForm()
        profile_form = TenantProfileForm()
        
    # Filter properties for this owner
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    profile_form.fields['pg_property'].queryset = properties
    profile_form.fields['room'].queryset = Room.objects.none()
        
    return render(request, 'owner/tenant_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Onboard New Tenant'
    })

@login_required
def load_rooms(request):
    property_id = request.GET.get('property_id')
    rooms = Room.objects.filter(pg_property_id=property_id, is_active=True).order_by('room_number')
    
    # Only return rooms that have available capacity
    available_rooms = [r for r in rooms if r.available_beds > 0]
    
    return JsonResponse(list({'id': r.id, 'name': f"Room {r.room_number} ({r.available_beds} beds left)"} for r in available_rooms), safe=False)

@login_required
def tenant_shift(request, pk):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    tenant = get_object_or_404(Tenant, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        room_id = request.POST.get('room')
        if room_id:
            room = get_object_or_404(Room, pk=room_id, pg_property__owner=request.user.pg_owner_profile)
            if room.available_beds > 0:
                tenant.room = room
                tenant.pg_property = room.pg_property
                tenant.save()
                messages.success(request, f"Tenant shifted to Room {room.room_number} successfully.")
                return redirect('tenants_list')
            else:
                messages.error(request, "Selected room is full.")
                
    return render(request, 'owner/tenant_shift.html', {
        'tenant': tenant,
        'properties': properties,
    })
