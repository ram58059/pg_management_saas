from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice, Payment, PropertyPaymentSettings, PaymentProof, RoomElectricityBill, GeneratedInvoice
from apps.tenants.models import Tenant, TenantDue
from apps.properties.models import Property, Room
from .forms import PaymentForm, InvoiceForm, PropertyPaymentSettingsForm, PaymentProofForm
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
import json

@login_required
def invoice_list(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    invoices = Invoice.objects.filter(tenant__pg_property__owner=request.user.pg_owner_profile).order_by('-created_at')
    return render(request, 'owner/invoices.html', {'invoices': invoices})

@login_required
def generate_monthly_invoices(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    if request.method == 'POST':
        month = request.POST.get('billing_month')
        if not month:
            messages.error(request, "Please select a billing month.")
            return redirect('invoice_list')
            
        import datetime
        billing_date = datetime.datetime.strptime(month, '%Y-%m').date()
        due_date = billing_date.replace(day=5)
        
        tenants = Tenant.objects.filter(pg_property__owner=request.user.pg_owner_profile, is_active=True)
        count = 0
        
        for tenant in tenants:
            # Check if invoice already exists
            if not Invoice.objects.filter(tenant=tenant, billing_month__year=billing_date.year, billing_month__month=billing_date.month).exists():
                Invoice.objects.create(
                    tenant=tenant,
                    billing_month=billing_date,
                    rent_amount=tenant.room.base_rent,
                    due_date=due_date
                )
                count += 1
                
        messages.success(request, f"Successfully generated {count} invoices for {billing_date.strftime('%b %Y')}.")
        return redirect('invoice_list')
        
    return redirect('invoice_list')

@login_required
def payment_create(request, invoice_id):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    invoice = get_object_or_404(Invoice, pk=invoice_id, tenant__pg_property__owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            messages.success(request, f"Payment of ₹{payment.amount} recorded successfully.")
            return redirect('invoice_list')
    else:
        form = PaymentForm(initial={'amount': invoice.remaining_due, 'payment_date': timezone.now().date()})
        
    return render(request, 'owner/payment_form.html', {
        'form': form,
        'invoice': invoice
    })

@login_required
def electricity_bills_manager(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    selected_property_id = request.GET.get('property')
    billing_month_str = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    
    import datetime
    try:
        billing_date = datetime.datetime.strptime(billing_month_str, '%Y-%m').date()
    except ValueError:
        billing_date = timezone.now().date().replace(day=1)
        billing_month_str = billing_date.strftime('%Y-%m')
        
    rooms_data = []
    
    if request.method == 'POST':
        # AJAX form submission for a specific room
        import json
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            previous_reading = float(data.get('previous_reading'))
            current_reading = float(data.get('current_reading'))
            
            room = Room.objects.get(id=room_id, pg_property__owner=request.user.pg_owner_profile)
            
            if current_reading < previous_reading:
                return JsonResponse({'error': 'Current reading cannot be less than previous reading.'}, status=400)
                
            active_tenants = room.tenants.filter(is_active=True)
            occupied_count = active_tenants.count()
            
            if occupied_count == 0:
                return JsonResponse({'error': 'No active tenants in this room.'}, status=400)
                
            units_used = current_reading - previous_reading
            cost_per_unit = room.pg_property.electricity_cost_per_unit
            total_amount = units_used * float(cost_per_unit)
            split_amount = total_amount / occupied_count
            
            # Check for duplicate
            if RoomElectricityBill.objects.filter(room=room, billing_month__year=billing_date.year, billing_month__month=billing_date.month).exists():
                return JsonResponse({'error': 'Electricity bill for this room and month already exists.'}, status=400)
                
            with transaction.atomic():
                # 1. Create RoomElectricityBill
                bill = RoomElectricityBill.objects.create(
                    pg_property=room.pg_property,
                    room=room,
                    previous_reading=previous_reading,
                    current_reading=current_reading,
                    units_used=units_used,
                    cost_per_unit=cost_per_unit,
                    total_amount=total_amount,
                    split_amount=split_amount,
                    billing_month=billing_date,
                    created_by=request.user
                )
                
                # 2. Create TenantDue for each active tenant
                month_identifier = f"EB for {billing_date.strftime('%B %Y')}"
                for tenant in active_tenants:
                    TenantDue.objects.create(
                        tenant=tenant,
                        amount=split_amount,
                        reason='ELECTRICITY',
                        description=month_identifier,
                        due_date=timezone.now().date().replace(day=5), # default due date
                        status='PENDING'
                    )
            
            return JsonResponse({'status': 'SUCCESS', 'message': f'EB calculated and dues created for {occupied_count} tenants.'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    if selected_property_id:
        property_obj = get_object_or_404(Property, id=selected_property_id, owner=request.user.pg_owner_profile)
        rooms = property_obj.rooms.filter(is_active=True).order_by('room_number')
        
        for room in rooms:
            occupied_count = room.tenants.filter(is_active=True).count()
            
            # Check if bill already generated for this month
            is_generated = RoomElectricityBill.objects.filter(
                room=room, 
                billing_month__year=billing_date.year, 
                billing_month__month=billing_date.month
            ).exists()
            
            # Get previous month's reading to pre-fill
            prev_bill = RoomElectricityBill.objects.filter(room=room).order_by('-billing_month', '-created_at').first()
            previous_reading = prev_bill.current_reading if prev_bill else 0
            
            rooms_data.append({
                'room': room,
                'occupied_count': occupied_count,
                'is_generated': is_generated,
                'previous_reading': previous_reading,
                'cost_per_unit': property_obj.electricity_cost_per_unit
            })
            
    return render(request, 'owner/electricity_bills.html', {
        'properties': properties,
        'selected_property_id': int(selected_property_id) if selected_property_id else None,
        'billing_month': billing_month_str,
        'rooms_data': rooms_data
    })

@login_required
def view_receipt(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    # Check permissions
    if request.user.is_tenant() and invoice.tenant.user != request.user:
        return redirect('tenant_dashboard')
    elif request.user.is_owner() and invoice.tenant.pg_property.owner != request.user.pg_owner_profile:
        return redirect('owner_dashboard')
        
    payments = invoice.payments.filter(status='APPROVED').order_by('-payment_date')
    
    return render(request, 'receipt.html', {
        'invoice': invoice,
        'payments': payments
    })

@login_required
def payment_settings(request):
    if not request.user.is_owner():
        return redirect('tenant_login')
        
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    selected_property_id = request.GET.get('property')
    settings = None
    form = None
    
    if selected_property_id:
        property_obj = get_object_or_404(Property, pk=selected_property_id, owner=request.user.pg_owner_profile)
        settings = PropertyPaymentSettings.objects.filter(pg_property=property_obj).first()
        
        if request.method == 'POST':
            form = PropertyPaymentSettingsForm(request.POST, request.FILES, instance=settings)
            if form.is_valid():
                new_settings = form.save(commit=False)
                new_settings.pg_property = property_obj
                new_settings.save()
                messages.success(request, "Payment settings updated successfully.")
                return redirect(f"{request.path}?property={selected_property_id}")
        else:
            form = PropertyPaymentSettingsForm(instance=settings)
            
    return render(request, 'owner/payment_settings.html', {
        'properties': properties,
        'selected_property_id': int(selected_property_id) if selected_property_id else None,
        'form': form,
        'settings': settings
    })

@login_required
def payment_verifications(request):
    if not request.user.is_owner():
        return redirect('tenant_login')
        
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    
    # Get filters
    search_query = request.GET.get('q', '')
    selected_property_id = request.GET.get('property', '')
    status_filter = request.GET.get('status', 'IN_VERIFICATION')
    month_filter = request.GET.get('month', '')
    date_filter = request.GET.get('date', '')
    
    payments = Payment.objects.filter(
        Q(invoice__tenant__pg_property__owner=request.user.pg_owner_profile) |
        Q(tenant_due__tenant__pg_property__owner=request.user.pg_owner_profile) |
        Q(tenant__pg_property__owner=request.user.pg_owner_profile)
    ).distinct().order_by('-created_at')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
        
    if search_query:
        payments = payments.filter(
            Q(invoice__tenant__user__first_name__icontains=search_query) |
            Q(invoice__tenant__user__last_name__icontains=search_query) |
            Q(tenant_due__tenant__user__first_name__icontains=search_query) |
            Q(tenant_due__tenant__user__last_name__icontains=search_query) |
            Q(tenant__user__first_name__icontains=search_query) |
            Q(tenant__user__last_name__icontains=search_query)
        )
        
    if selected_property_id:
        payments = payments.filter(
            Q(invoice__tenant__pg_property_id=selected_property_id) |
            Q(tenant_due__tenant__pg_property_id=selected_property_id) |
            Q(tenant__pg_property_id=selected_property_id)
        )
        
    if month_filter:
        payments = payments.filter(created_at__month=month_filter.split('-')[1], created_at__year=month_filter.split('-')[0])
        
    if date_filter:
        payments = payments.filter(created_at__date=date_filter)
        
    paginator = Paginator(payments, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'owner/payment_verifications.html', {
        'properties': properties,
        'selected_property_id': int(selected_property_id) if selected_property_id else None,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'month_filter': month_filter,
        'date_filter': date_filter
    })

@login_required
def verify_payment(request, payment_id):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json'
    
    if not request.user.is_owner():
        if is_ajax:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        return redirect('tenant_login')
        
    payment = get_object_or_404(Payment, pk=payment_id)
    
    # Check permissions
    owner = request.user.pg_owner_profile
    is_valid = False
    if payment.invoice and payment.invoice.tenant.pg_property.owner == owner:
        is_valid = True
    elif payment.tenant_due and payment.tenant_due.tenant.pg_property.owner == owner:
        is_valid = True
    elif payment.tenant and payment.tenant.pg_property.owner == owner:
        is_valid = True
        
    if not is_valid:
        if is_ajax:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        return redirect('tenant_login')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            rejection_reason = data.get('rejection_reason', '')
        except (json.JSONDecodeError, TypeError):
            action = request.POST.get('action')
            rejection_reason = request.POST.get('rejection_reason', '')
            
        proof = payment.proof
        
        if action == 'APPROVE':
            payment.status = 'SUCCESS'
            proof.verified_by = request.user
            proof.verified_at = timezone.now()
            proof.save()
            payment.save()
            if is_ajax:
                return JsonResponse({'status': 'SUCCESS', 'message': f'Payment #{payment.id} verified and approved.'})
            messages.success(request, f"Payment #{payment.id} verified and approved.")
            
        elif action == 'REJECT':
            payment.status = 'REJECTED'
            proof.verified_by = request.user
            proof.rejected_at = timezone.now()
            proof.rejection_reason = rejection_reason
            proof.save()
            payment.save()
            if is_ajax:
                return JsonResponse({'status': 'REJECTED', 'message': f'Payment #{payment.id} rejected.'})
            messages.success(request, f"Payment #{payment.id} rejected.")
            
    return redirect('payment_verifications')

@login_required
def tenant_payments(request):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    tenant = request.user.tenant_profile
    # We show generated PDF invoices here as per the new requirement
    invoices = GeneratedInvoice.objects.filter(tenant=tenant).select_related('payment').order_by('-generated_at')
    
    return render(request, 'tenant/payments.html', {
        'invoices': invoices
    })

@login_required
def download_invoice(request, invoice_id):
    invoice = get_object_or_404(GeneratedInvoice, pk=invoice_id)
    
    # Security check: Only the tenant or the owner can download it
    is_authorized = False
    if request.user.is_tenant() and invoice.tenant.user == request.user:
        is_authorized = True
    elif request.user.is_owner() and invoice.pg_property.owner == request.user.pg_owner_profile:
        is_authorized = True
        
    if not is_authorized:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        messages.error(request, 'Unauthorized to download this invoice.')
        return redirect('tenant_dashboard' if request.user.is_tenant() else 'owner_dashboard')
        
    if not invoice.pdf_file:
        messages.error(request, 'Invoice PDF not generated yet.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    # Redirect to S3 URL for download
    return redirect(invoice.pdf_file.url)

@login_required
def tenant_pay_rent(request, invoice_id):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    invoice = get_object_or_404(Invoice, pk=invoice_id, tenant=request.user.tenant_profile)
    settings = PropertyPaymentSettings.objects.filter(pg_property=invoice.tenant.pg_property).first()
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        
        # Create a pending payment
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method='UPI',
            status='PENDING'
        )
        return redirect('tenant_payment_page', payment_id=payment.id)
        
    return render(request, 'tenant/pay_rent.html', {
        'invoice': invoice,
        'settings': settings,
        'remaining_due': invoice.remaining_due
    })

@login_required
def tenant_payment_intent(request):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    tenant = request.user.tenant_profile
    
    # Calculate total due
    total_invoice_due = sum(inv.remaining_due for inv in tenant.invoices.filter(status__in=['PENDING', 'PARTIAL']))
    total_dues = tenant.dues.filter(status__in=['PENDING', 'PARTIAL']).aggregate(total=Sum('amount'))['total'] or 0
    
    active_due = total_invoice_due + total_dues
    
    if active_due <= 0:
        messages.info(request, "You have no pending dues.")
        return redirect('tenant_dashboard')
        
    payment = Payment.objects.create(
        tenant=tenant,
        amount=active_due,
        payment_method='UPI',
        status='PENDING'
    )
    
    return redirect('tenant_payment_page', payment_id=payment.id)

@login_required
def tenant_payment_page(request, payment_id):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    payment = get_object_or_404(Payment, pk=payment_id)
    tenant = request.user.tenant_profile
    
    if (payment.invoice and payment.invoice.tenant != tenant) or \
       (payment.tenant_due and payment.tenant_due.tenant != tenant) or \
       (payment.tenant and payment.tenant != tenant):
        return redirect('tenant_dashboard')
        
    settings = PropertyPaymentSettings.objects.filter(pg_property=tenant.pg_property).first()
    
    # Check if a proof already exists (in case they went back or are re-uploading a rejected payment)
    existing_proof = getattr(payment, 'proof', None)
    
    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=existing_proof)
        if form.is_valid():
            with transaction.atomic():
                proof = form.save(commit=False)
                proof.payment = payment
                proof.save()
                
                payment.status = 'IN_VERIFICATION'
                payment.save()
                
            messages.success(request, "Payment proof uploaded successfully. Waiting for verification.")
            return redirect('tenant_dashboard')
    else:
        form = PaymentProofForm(instance=existing_proof)
        
    return render(request, 'tenant/payment_page.html', {
        'payment': payment,
        'form': form,
        'settings': settings
    })

@login_required
def tenant_payment_history(request):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    tenant = request.user.tenant_profile
    payments = Payment.objects.filter(
        Q(invoice__tenant=tenant) |
        Q(tenant_due__tenant=tenant) |
        Q(tenant=tenant)
    ).distinct().order_by('-created_at')
    
    return render(request, 'tenant/payment_history.html', {
        'payments': payments
    })
