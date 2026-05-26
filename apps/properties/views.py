from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Property, Room
from .forms import PropertyForm, RoomForm

@login_required
def properties_list(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    properties = Property.objects.filter(owner=request.user.pg_owner_profile).order_by('-created_at')
    
    # Calculate some stats
    for prop in properties:
        prop.total_rooms = prop.rooms.count()
        prop.total_capacity = sum(r.capacity for r in prop.rooms.all())
        prop.occupied_beds = sum(r.occupied_beds for r in prop.rooms.all())
        
    return render(request, 'owner/properties.html', {'properties': properties})

@login_required
def property_create(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save(commit=False)
            property.owner = request.user.pg_owner_profile
            property.save()
            messages.success(request, f"Property '{property.name}' added successfully.")
            return redirect('properties_list')
    else:
        form = PropertyForm()
        
    return render(request, 'owner/property_form.html', {'form': form, 'title': 'Add Property'})

@login_required
def property_update(request, pk):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    property = get_object_or_404(Property, pk=pk, owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            form.save()
            messages.success(request, f"Property '{property.name}' updated successfully.")
            return redirect('properties_list')
    else:
        form = PropertyForm(instance=property)
        
    return render(request, 'owner/property_form.html', {'form': form, 'title': 'Edit Property'})

@login_required
def property_delete(request, pk):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    property = get_object_or_404(Property, pk=pk, owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        property.delete()
        messages.success(request, f"Property '{property.name}' deleted successfully.")
        return redirect('properties_list')
        
    return render(request, 'owner/property_confirm_delete.html', {'property': property})

@login_required
def rooms_list(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    selected_property_id = request.GET.get('property')
    
    if selected_property_id:
        rooms = Room.objects.filter(pg_property_id=selected_property_id, pg_property__owner=request.user.pg_owner_profile).select_related('pg_property')
    else:
        rooms = Room.objects.filter(pg_property__owner=request.user.pg_owner_profile).select_related('pg_property')
        
    rooms = rooms.order_by('pg_property__name', 'room_number')
    
    return render(request, 'owner/rooms.html', {
        'rooms': rooms,
        'properties': properties,
        'selected_property_id': int(selected_property_id) if selected_property_id else None
    })

@login_required
def room_create(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    if request.method == 'POST':
        form = RoomForm(request.user.pg_owner_profile, request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"Room {room.room_number} added successfully.")
            return redirect('rooms_list')
    else:
        form = RoomForm(request.user.pg_owner_profile)
        
    return render(request, 'owner/room_form.html', {'form': form, 'title': 'Add Room'})

@login_required
def room_update(request, pk):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    room = get_object_or_404(Room, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        form = RoomForm(request.user.pg_owner_profile, request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"Room {room.room_number} updated successfully.")
            return redirect('rooms_list')
    else:
        form = RoomForm(request.user.pg_owner_profile, instance=room)
        
    return render(request, 'owner/room_form.html', {'form': form, 'title': 'Edit Room'})

@login_required
def room_delete(request, pk):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    room = get_object_or_404(Room, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        room.delete()
        messages.success(request, f"Room {room.room_number} deleted successfully.")
        return redirect('rooms_list')
        
    return render(request, 'owner/room_confirm_delete.html', {'room': room})
