from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tenants.models import Tenant
from apps.tenants.services.rent_dues import ensure_monthly_rent_dues, sync_standard_due_dates


class Command(BaseCommand):
    help = 'Automatically generates monthly rent dues for all active tenants.'

    def handle(self, *args, **options):
        billing_date = timezone.localdate().replace(day=1)

        self.stdout.write(
            self.style.NOTICE(
                f'Generating monthly rent dues for {billing_date.strftime("%B %Y")}...'
            )
        )

        created_count, skipped_count = ensure_monthly_rent_dues(billing_date=billing_date)

        for tenant in Tenant.objects.filter(is_active=True):
            sync_standard_due_dates(tenant)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {created_count} rent dues. Skipped {skipped_count} tenants.'
            )
        )
