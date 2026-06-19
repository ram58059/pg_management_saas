from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from apps.accounts.models import CustomUser
from apps.properties.models import Property, Room
from django.db.models import Sum, Q, DecimalField
from django.db.models.functions import Coalesce
from .models import Tenant, TenantDue, TenantDocument
from .forms import TenantUserForm, TenantProfileForm, TenantDueForm
from .services.tenant_creation import create_tenant_from_forms, setup_tenant_onboarding_forms
from .services.room_options import get_available_rooms_for_property
from django.http import JsonResponse
import json

from django.core.paginator import Paginator

@login_required
def tenants_list(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    tenants = Tenant.objects.filter(pg_property__owner=request.user.pg_owner_profile).select_related(
        'user', 'room', 'pg_property'
    ).annotate(
        total_pending_due=Coalesce(
            Sum('dues__amount', filter=Q(dues__status='PENDING') | Q(dues__status='PARTIAL')),
            0,
            output_field=DecimalField()
        )
    )
    
    # Get filters
    q = request.GET.get('q', '').strip()
    property_filter = request.GET.get('property', '')
    room_filter = request.GET.get('room_number', '')
    show_inactive = request.GET.get('show_inactive', 'false') == 'true'
    joined_sort = request.GET.get('joined', 'desc')
    has_due = request.GET.get('due', '')
    
    # Apply filters
    if q:
        tenants = tenants.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(user__phone_number__icontains=q)
        )
    if property_filter:
        tenants = tenants.filter(pg_property__name=property_filter)
    if room_filter:
        tenants = tenants.filter(room__room_number=room_filter)
        
    if show_inactive:
        tenants = tenants.filter(is_active=False)
    else:
        tenants = tenants.filter(is_active=True)
            
    if has_due == 'true':
        tenants = tenants.filter(total_pending_due__gt=0)
        
    # Sorting
    if joined_sort == 'asc':
        tenants = tenants.order_by('date_of_joining', 'id')
    else:
        tenants = tenants.order_by('-date_of_joining', '-id')
        
    # Pagination
    paginator = Paginator(tenants, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    # Get unique room numbers for the filter based on selected property
    if property_filter:
        rooms = Room.objects.filter(
            pg_property__owner=request.user.pg_owner_profile, 
            pg_property__name=property_filter
        ).values_list('room_number', flat=True).distinct().order_by('room_number')
    else:
        rooms = []
    
    due_form = TenantDueForm()
    
    return render(request, 'owner/tenants.html', {
        'tenants': page_obj,
        'page_obj': page_obj,
        'properties': properties,
        'rooms': rooms,
        'due_form': due_form,
        'current_filters': {
            'q': q,
            'property': property_filter,
            'room_number': room_filter,
            'show_inactive': str(show_inactive).lower(),
            'joined': joined_sort,
            'due': has_due,
        }
    })

@login_required
def tenant_create(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')

    owner = request.user.pg_owner_profile

    if request.method == 'POST':
        user_form, profile_form = setup_tenant_onboarding_forms(
            owner=owner,
            post_data=request.POST,
            files=request.FILES,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user, tenant, password = create_tenant_from_forms(user_form, profile_form)
            messages.success(request, f"Tenant {user.get_full_name()} onboarded successfully.")
            return redirect('tenants_list')
    else:
        user_form, profile_form = setup_tenant_onboarding_forms(owner=owner)

    return render(request, 'owner/tenant_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Onboard New Tenant',
        'cancel_url': 'tenants_list',
    })


def public_tenant_onboard(request):
    if request.user.is_authenticated:
        if request.user.is_owner():
            return redirect('owner_dashboard')
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        user_form, profile_form = setup_tenant_onboarding_forms(
            post_data=request.POST,
            files=request.FILES,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user, tenant, password = create_tenant_from_forms(user_form, profile_form)
            fresh_user_form, fresh_profile_form = setup_tenant_onboarding_forms()
            return render(request, 'tenant/onboarding.html', {
                'user_form': fresh_user_form,
                'profile_form': fresh_profile_form,
                'onboard_credentials': {
                    'username': user.username,
                    'password': password,
                    'full_name': user.get_full_name(),
                },
                'show_success_modal': True,
            })

        return render(request, 'tenant/onboarding.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'onboard_credentials': None,
            'show_success_modal': False,
        })

    user_form, profile_form = setup_tenant_onboarding_forms()
    return render(request, 'tenant/onboarding.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'onboard_credentials': None,
        'show_success_modal': False,
    })

def load_rooms(request):
    property_id = request.GET.get('property_id')
    return JsonResponse(get_available_rooms_for_property(property_id), safe=False)

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

@login_required
def api_tenant_dues_list(request, pk):
    if not request.user.is_owner():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tenant = get_object_or_404(Tenant, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    dues = TenantDue.objects.filter(tenant=tenant).order_by('-due_date')
    
    data = []
    for due in dues:
        data.append({
            'id': due.id,
            'amount': str(due.amount),
            'reason': due.get_reason_display(),
            'custom_reason': due.custom_reason,
            'description': due.description,
            'due_date': due.due_date.strftime('%Y-%m-%d'),
            'status': due.status,
            'status_display': due.get_status_display()
        })
        
    return JsonResponse({'dues': data})

@login_required
def api_tenant_due_save(request, pk):
    if not request.user.is_owner() or request.method != 'POST':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tenant = get_object_or_404(Tenant, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    
    try:
        data = json.loads(request.body)
        due_id = data.get('id')
        
        if due_id:
            due = get_object_or_404(TenantDue, pk=due_id, tenant=tenant)
            form = TenantDueForm(data, instance=due)
        else:
            form = TenantDueForm(data)
            
        if form.is_valid():
            due = form.save(commit=False)
            due.tenant = tenant
            due.save()
            return JsonResponse({'success': True, 'id': due.id})
        else:
            return JsonResponse({'error': 'Validation failed', 'errors': form.errors}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def api_tenant_due_delete(request, pk, due_id):
    if not request.user.is_owner() or request.method != 'POST':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tenant = get_object_or_404(Tenant, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    due = get_object_or_404(TenantDue, pk=due_id, tenant=tenant)
    due.delete()
    
    return JsonResponse({'success': True})
@login_required
def api_tenant_details(request, pk):
    if not request.user.is_owner():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tenant = get_object_or_404(
        Tenant.objects.select_related('user', 'pg_property', 'room'), 
        pk=pk, 
        pg_property__owner=request.user.pg_owner_profile
    )
    
    pending_dues = tenant.dues.filter(status__in=['PENDING', 'PARTIAL']).aggregate(Sum('amount'))['amount__sum'] or 0
    electricity_dues = tenant.dues.filter(reason='ELECTRICITY', status__in=['PENDING', 'PARTIAL']).aggregate(Sum('amount'))['amount__sum'] or 0
    
    documents = tenant.documents.all()
    doc_data = []
    for doc in documents:
        doc_data.append({
            'type': doc.document_type,
            'url': doc.file.url if doc.file else None
        })
        
    data = {
        'id': tenant.id,
        'first_name': tenant.user.first_name,
        'last_name': tenant.user.last_name,
        'full_name': tenant.user.get_full_name(),
        'phone_number': tenant.user.phone_number,
        'email': tenant.user.email,
        'username': tenant.user.username,
        'emergency_contact_name': tenant.emergency_contact_name,
        'emergency_contact_number': tenant.emergency_contact_number,
        'emergency_contact': f"{tenant.emergency_contact_name} ({tenant.emergency_contact_number})",
        
        'property_id': tenant.pg_property.id if tenant.pg_property else '',
        'property_name': tenant.pg_property.name if tenant.pg_property else 'N/A',
        'room_id': tenant.room.id if tenant.room else '',
        'room_number': tenant.room.room_number if tenant.room else 'N/A',
        'sharing_type': (f"{tenant.room.capacity} Sharing" if tenant.room.capacity > 1 else "Single") if tenant.room else 'N/A',
        'join_date': tenant.date_of_joining.strftime('%Y-%m-%d') if tenant.date_of_joining else '',
        'join_date_display': tenant.date_of_joining.strftime('%d %b %Y') if tenant.date_of_joining else 'N/A',
        'status': 'Active' if tenant.is_active else 'Inactive',
        
        'monthly_rent': str(tenant.room.base_rent) if tenant.room else '0',
        'pending_dues': str(pending_dues),
        'deposit_amount': str(tenant.deposit_amount),
        'electricity_dues': str(electricity_dues),
        
        'id_proof_type': tenant.get_id_proof_type_display() if hasattr(tenant, 'get_id_proof_type_display') else tenant.id_proof_type,
        'id_proof_number': tenant.id_proof_number,
        'documents': doc_data,
        'profile_photo_url': tenant.profile_photo.url if tenant.profile_photo else None
    }
    
    return JsonResponse(data)

@login_required
def api_tenant_update(request, pk):
    if not request.user.is_owner() or request.method != 'POST':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tenant = get_object_or_404(Tenant, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    user = tenant.user
    
    try:
        with transaction.atomic():
            # Update User
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            
            # Email and Phone strict uniqueness validation removed as requested
                
            if first_name: user.first_name = first_name
            if last_name: user.last_name = last_name
            if phone: user.phone_number = phone
            user.email = email # Update email directly to allow clearing if empty
            if password: user.set_password(password)
            user.save()
            
            # Update Profile
            tenant.emergency_contact_name = request.POST.get('emergency_contact_name', tenant.emergency_contact_name)
            tenant.emergency_contact_number = request.POST.get('emergency_contact_number', tenant.emergency_contact_number)
            
            deposit_amount = request.POST.get('deposit_amount')
            if deposit_amount: tenant.deposit_amount = deposit_amount
            
            join_date = request.POST.get('date_of_joining')
            if join_date: tenant.date_of_joining = join_date
            
            status = request.POST.get('status')
            if status == 'Active':
                tenant.is_active = True
            elif status in ['Inactive', 'Vacated']:
                tenant.is_active = False
            
            id_proof_type = request.POST.get('id_proof_type')
            if id_proof_type: tenant.id_proof_type = id_proof_type
            
            id_proof_number = request.POST.get('id_proof_number')
            if id_proof_number: tenant.id_proof_number = id_proof_number
            
            profile_photo = request.FILES.get('profile_photo')
            if profile_photo:
                tenant.profile_photo = profile_photo
            
            # Handle Room Update
            new_room_id = request.POST.get('room')
            if new_room_id and str(new_room_id) != str(tenant.room_id):
                new_room = get_object_or_404(Room, pk=new_room_id, pg_property__owner=request.user.pg_owner_profile)
                if new_room.available_beds <= 0 and tenant.is_active:
                    return JsonResponse({'error': 'Selected room is full.'}, status=400)
                tenant.room = new_room
                tenant.pg_property = new_room.pg_property
                
            # Perform save. If profile photo is immutable and changed, this will raise ValidationError from clean()
            try:
                tenant.save()
            except ValidationError as ve:
                if 'profile_photo' in ve.error_dict:
                    return JsonResponse({'error': ve.error_dict['profile_photo'][0].message}, status=400)
                raise ve
            
            # Handle Document Replace
            id_proof_file = request.FILES.get('id_proof_file')
            if id_proof_file:
                # Find existing ID proof
                doc = tenant.documents.filter(document_type__in=['AADHAAR', 'PAN', 'PASSPORT', 'ID_PROOF']).first()
                if doc:
                    doc.document_type = tenant.id_proof_type or 'ID_PROOF'
                    doc.file = id_proof_file
                    doc.save()
                else:
                    TenantDocument.objects.create(
                        tenant=tenant,
                        document_type=tenant.id_proof_type or 'ID_PROOF',
                        file=id_proof_file
                    )
                    
            return JsonResponse({'success': True})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def api_tenant_delete(request, pk):
    if not request.user.is_owner() or request.method != 'POST':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    tenant = get_object_or_404(Tenant, pk=pk, pg_property__owner=request.user.pg_owner_profile)
    
    try:
        tenant.is_active = False
        tenant.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

