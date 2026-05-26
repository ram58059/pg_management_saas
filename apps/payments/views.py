from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice, Payment, ElectricityBill, PropertyPaymentSettings, PaymentProof
from apps.tenants.models import Tenant
from apps.properties.models import Property
from .forms import PaymentForm, InvoiceForm, ElectricityBillForm, PropertyPaymentSettingsForm, PaymentProofForm
from django.utils import timezone
from django.db import transaction

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
def electricity_bill_create(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    properties = Property.objects.filter(owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        form = ElectricityBillForm(request.POST)
        property_id = request.POST.get('pg_property')
        
        if form.is_valid() and property_id:
            pg_property = get_object_or_404(Property, pk=property_id, owner=request.user.pg_owner_profile)
            bill = form.save(commit=False)
            bill.pg_property = pg_property
            
            # Find active tenants in this property
            active_tenants = Tenant.objects.filter(pg_property=pg_property, is_active=True)
            tenant_count = active_tenants.count()
            
            if tenant_count > 0:
                bill.per_tenant_amount = bill.total_bill_amount / tenant_count
                bill.save()
                
                # Add this amount to their latest pending invoice or create a new one
                for tenant in active_tenants:
                    # Try to find invoice for the same month
                    invoice = Invoice.objects.filter(
                        tenant=tenant, 
                        billing_month__year=bill.billing_month.year,
                        billing_month__month=bill.billing_month.month
                    ).first()
                    
                    if invoice:
                        invoice.electricity_amount = bill.per_tenant_amount
                        invoice.save()
                        
                messages.success(request, f"Electricity bill allocated. ₹{bill.per_tenant_amount} added to {tenant_count} tenants.")
                return redirect('invoice_list')
            else:
                messages.error(request, "No active tenants found in this property to allocate the bill.")
    else:
        form = ElectricityBillForm()
        
    return render(request, 'owner/electricity_bill_form.html', {
        'form': form,
        'properties': properties
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
    selected_property_id = request.GET.get('property')
    
    payments = Payment.objects.filter(
        invoice__tenant__pg_property__owner=request.user.pg_owner_profile,
        status='SCREENSHOT_UPLOADED'
    ).order_by('created_at')
    
    if selected_property_id:
        payments = payments.filter(invoice__tenant__pg_property_id=selected_property_id)
        
    return render(request, 'owner/payment_verifications.html', {
        'properties': properties,
        'selected_property_id': int(selected_property_id) if selected_property_id else None,
        'payments': payments
    })

@login_required
def verify_payment(request, payment_id):
    if not request.user.is_owner():
        return redirect('tenant_login')
        
    payment = get_object_or_404(Payment, pk=payment_id, invoice__tenant__pg_property__owner=request.user.pg_owner_profile)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        proof = payment.proof
        
        if action == 'APPROVE':
            payment.status = 'APPROVED'
            proof.verified_by = request.user
            proof.verified_at = timezone.now()
            proof.save()
            payment.save()
            messages.success(request, f"Payment #{payment.id} verified and approved.")
        elif action == 'REJECT':
            rejection_reason = request.POST.get('rejection_reason')
            payment.status = 'REJECTED'
            proof.verified_by = request.user
            proof.verified_at = timezone.now()
            proof.rejection_reason = rejection_reason
            proof.save()
            payment.save()
            messages.success(request, f"Payment #{payment.id} rejected.")
            
    return redirect('payment_verifications')

@login_required
def tenant_payments(request):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    tenant = request.user.tenant_profile
    invoices = Invoice.objects.filter(tenant=tenant).order_by('-created_at')
    
    return render(request, 'tenant/payments.html', {
        'invoices': invoices
    })

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
            status='PENDING',
            payment_date=timezone.now().date()
        )
        return redirect('tenant_upload_proof', payment_id=payment.id)
        
    return render(request, 'tenant/pay_rent.html', {
        'invoice': invoice,
        'settings': settings,
        'remaining_due': invoice.remaining_due
    })

@login_required
def tenant_upload_proof(request, payment_id):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    payment = get_object_or_404(Payment, pk=payment_id, invoice__tenant=request.user.tenant_profile)
    
    # Check if a proof already exists (in case they went back or are re-uploading a rejected payment)
    existing_proof = getattr(payment, 'proof', None)
    
    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=existing_proof)
        if form.is_valid():
            with transaction.atomic():
                proof = form.save(commit=False)
                proof.payment = payment
                proof.save()
                
                payment.status = 'SCREENSHOT_UPLOADED'
                payment.save()
                
            messages.success(request, "Payment proof uploaded successfully. Waiting for verification.")
            return redirect('tenant_payment_history')
    else:
        form = PaymentProofForm(instance=existing_proof)
        
    return render(request, 'tenant/upload_proof.html', {
        'payment': payment,
        'form': form
    })

@login_required
def tenant_payment_history(request):
    if not request.user.is_tenant():
        return redirect('owner_login')
        
    payments = Payment.objects.filter(invoice__tenant=request.user.tenant_profile).order_by('-created_at')
    
    return render(request, 'tenant/payment_history.html', {
        'payments': payments
    })
