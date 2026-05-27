from django.db.models import Q
from .models import Payment

def pending_verifications_count(request):
    if request.user.is_authenticated and hasattr(request.user, 'pg_owner_profile'):
        count = Payment.objects.filter(
            Q(invoice__tenant__pg_property__owner=request.user.pg_owner_profile) |
            Q(tenant_due__tenant__pg_property__owner=request.user.pg_owner_profile) |
            Q(tenant__pg_property__owner=request.user.pg_owner_profile),
            status='IN_VERIFICATION'
        ).distinct().count()
        return {'pending_verifications_count': count}
    return {}
