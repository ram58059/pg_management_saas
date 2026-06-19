import calendar
from datetime import datetime

from django.utils import timezone

from apps.tenants.models import Tenant, TenantDue
from utils.billing import monthly_due_date

_AUTO_DUE_PREFIXES = ('Rent for ', 'EB for ')


def _month_identifier(billing_date):
    return f"Rent for {billing_date.strftime('%B %Y')}"


def _billing_month_from_description(description):
    if not description:
        return None
    for prefix in _AUTO_DUE_PREFIXES:
        if description.startswith(prefix):
            try:
                return datetime.strptime(description[len(prefix):], '%B %Y').date().replace(day=1)
            except ValueError:
                return None
    return None


def sync_standard_due_dates(tenant):
    """Align auto-generated rent/EB due dates to the 7th of the billing month."""
    dues = TenantDue.objects.filter(
        tenant=tenant,
        reason__in=['RENT', 'ELECTRICITY'],
        status__in=['PENDING', 'PARTIAL'],
    )

    for due in dues:
        billing_date = _billing_month_from_description(due.description)
        if not billing_date:
            continue

        expected_due_date = monthly_due_date(billing_date)
        if due.due_date != expected_due_date:
            due.due_date = expected_due_date
            due.save(update_fields=['due_date'])


def _tenant_eligible_for_rent(tenant, billing_date):
    if not tenant.is_active:
        return False
    if not tenant.room or tenant.room.base_rent <= 0:
        return False

    last_day = calendar.monthrange(billing_date.year, billing_date.month)[1]
    billing_month_end = billing_date.replace(day=last_day)
    return tenant.date_of_joining <= billing_month_end


def ensure_monthly_rent_due(tenant, billing_date=None):
    """Create the monthly rent due for a tenant when missing."""
    billing_date = billing_date or timezone.localdate().replace(day=1)
    month_identifier = _month_identifier(billing_date)

    if not _tenant_eligible_for_rent(tenant, billing_date):
        return None

    expected_due_date = monthly_due_date(billing_date)
    expected_amount = tenant.room.base_rent

    existing_due = TenantDue.objects.filter(
        tenant=tenant,
        reason='RENT',
        description=month_identifier,
    ).first()
    if existing_due:
        updates = {}
        if existing_due.due_date != expected_due_date:
            updates['due_date'] = expected_due_date
        if existing_due.amount != expected_amount:
            updates['amount'] = expected_amount
        if updates:
            for field, value in updates.items():
                setattr(existing_due, field, value)
            existing_due.save(update_fields=list(updates.keys()))
        return None

    return TenantDue.objects.create(
        tenant=tenant,
        amount=expected_amount,
        reason='RENT',
        description=month_identifier,
        due_date=expected_due_date,
        status='PENDING',
    )


def ensure_monthly_rent_dues(billing_date=None, tenants=None):
    """Ensure monthly rent dues exist for active tenants."""
    billing_date = billing_date or timezone.localdate().replace(day=1)
    queryset = tenants if tenants is not None else Tenant.objects.filter(is_active=True).select_related('room')

    created_count = 0
    skipped_count = 0

    for tenant in queryset:
        created = ensure_monthly_rent_due(tenant, billing_date)
        if created:
            created_count += 1
        else:
            skipped_count += 1

    return created_count, skipped_count
