from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tenants.models import Tenant, TenantDue
import datetime

class Command(BaseCommand):
    help = 'Automatically generates monthly rent dues for all active tenants.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        # Default billing month to the 1st of the current month
        billing_date = today.replace(day=1)
        
        self.stdout.write(self.style.NOTICE(f'Generating monthly rent dues for {billing_date.strftime("%B %Y")}...'))
        
        active_tenants = Tenant.objects.filter(is_active=True).select_related('room')
        
        created_count = 0
        skipped_count = 0
        
        for tenant in active_tenants:
            # Check if tenant has a room with base rent
            if not tenant.room or tenant.room.base_rent <= 0:
                self.stdout.write(self.style.WARNING(f'Skipped {tenant.user.get_full_name()}: No room or zero rent.'))
                skipped_count += 1
                continue
                
            # Determine due date (e.g. 5th of the month)
            due_date = billing_date.replace(day=5)
            
            # Check for existing rent due for this exact billing month string to prevent duplicates
            # Since TenantDue doesn't have a native billing_month column, we can use the `custom_reason` or `description` 
            # to store the month identifier, or we can just check if a RENT due exists that was created in the current month.
            
            # Best practice: We can set description to track the specific month
            month_identifier = f"Rent for {billing_date.strftime('%B %Y')}"
            
            existing_due = TenantDue.objects.filter(
                tenant=tenant,
                reason='RENT',
                description=month_identifier
            ).exists()
            
            if existing_due:
                skipped_count += 1
                continue
                
            # Create the due
            TenantDue.objects.create(
                tenant=tenant,
                amount=tenant.room.base_rent,
                reason='RENT',
                description=month_identifier,
                due_date=due_date,
                status='PENDING'
            )
            created_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {created_count} rent dues. Skipped {skipped_count} tenants.'))
