from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from apps.properties.models import Property, Room
from apps.tenants.models import Tenant
from apps.payments.models import Invoice, Payment
import datetime
from django.apps import apps

@login_required
def owner_dashboard(request):
    if not request.user.is_owner():
        return redirect('tenant_dashboard')
        
    owner = request.user.pg_owner_profile
    properties = Property.objects.filter(owner=owner)
    
    # Calculate stats
    properties_count = properties.count()
    
    rooms = Room.objects.filter(pg_property__owner=owner)
    total_capacity = sum(r.capacity for r in rooms)
    
    occupied_beds = Tenant.objects.filter(pg_property__owner=owner, is_active=True).count()
    vacant_beds = total_capacity - occupied_beds
    
    # Financials for current month
    today = datetime.date.today()
    invoices_this_month = Invoice.objects.filter(
        tenant__pg_property__owner=owner,
        billing_month__year=today.year,
        billing_month__month=today.month
    )
    
    revenue_this_month = invoices_this_month.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    pending_payments = invoices_this_month.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_payments -= revenue_this_month
    
    recent_payments = Payment.objects.filter(invoice__tenant__pg_property__owner=owner, status='APPROVED').order_by('-payment_date')[:5]
    upcoming_dues = Invoice.objects.filter(tenant__pg_property__owner=owner, status__in=['PENDING', 'PARTIAL']).order_by('due_date')[:5]
    
    context = {
        'properties_count': properties_count,
        'total_capacity': total_capacity,
        'occupied_beds': occupied_beds,
        'vacant_beds': vacant_beds,
        'revenue_this_month': revenue_this_month,
        'pending_payments': pending_payments,
        'recent_payments': recent_payments,
        'upcoming_dues': upcoming_dues,
    }
    return render(request, 'owner/dashboard.html', context)

@login_required
def tenant_dashboard(request):
    if not request.user.is_tenant():
        return redirect('owner_dashboard')
        
    tenant = request.user.tenant_profile
    invoices = Invoice.objects.filter(tenant=tenant).order_by('-billing_month')
    
    # Calculate active due from invoices
    active_due = sum(inv.remaining_due for inv in invoices if inv.status != 'PAID')
    
    # Calculate active due from ad-hoc TenantDues
    tenant_dues = apps.get_model('tenants', 'TenantDue').objects.filter(tenant=tenant).order_by('-due_date')
    pending_tenant_dues = tenant_dues.filter(status__in=['PENDING', 'PARTIAL']).aggregate(Sum('amount'))['amount__sum'] or 0
    active_due += pending_tenant_dues
    
    context = {
        'tenant': tenant,
        'room': tenant.room,
        'property': tenant.pg_property,
        'invoices': invoices,
        'active_due': active_due,
        'tenant_dues': tenant_dues,
        'pending_tenant_dues_total': pending_tenant_dues,
        'pending_tenant_dues_count': tenant_dues.filter(status__in=['PENDING', 'PARTIAL']).count(),
    }
    return render(request, 'tenant/dashboard.html', context)
