from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser, PGOwner
from apps.properties.models import Property, Room
from utils.file_uploads import get_tenant_document_upload_path, get_tenant_photo_upload_path
from utils.validators import validate_file_size, validate_image_extension, validate_document_extension

class Tenant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tenant_profile')
    pg_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, related_name='tenants')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, related_name='tenants')
    
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_number = models.CharField(max_length=15)
    
    id_proof_type = models.CharField(max_length=50, choices=[('AADHAAR', 'Aadhaar Card'), ('PAN', 'PAN Card'), ('PASSPORT', 'Passport')])
    id_proof_number = models.CharField(max_length=50)
    
    date_of_joining = models.DateField()
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    profile_photo = models.ImageField(upload_to=get_tenant_photo_upload_path, blank=True, null=True, validators=[validate_file_size, validate_image_extension])
    
    def clean(self):
        super().clean()
        if self.pk:
            old_tenant = Tenant.objects.get(pk=self.pk)
            # If the old tenant had a photo, and it's being changed or deleted, raise an error
            if getattr(self, '_skip_photo_lock', False):
                pass
            elif old_tenant.profile_photo and self.profile_photo != old_tenant.profile_photo:
                raise ValidationError({'profile_photo': 'Tenant photo is permanently locked after upload.'})
                
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.room}"

class TenantDue(models.Model):
    REASON_CHOICES = (
        ('RENT', 'Monthly Rent'),
        ('ELECTRICITY', 'Electricity Bill'),
        ('DEPOSIT', 'Security Deposit'),
        ('MAINTENANCE', 'Maintenance Charges'),
        ('DAMAGE', 'Damage Charges'),
        ('LATE_FEE', 'Late Payment'),
        ('FOOD', 'Food Charges'),
        ('OTHER', 'Other'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial'),
        ('CLEARED', 'Cleared'),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='dues')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    custom_reason = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TenantDocument(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50)
    file = models.FileField(upload_to=get_tenant_document_upload_path, validators=[validate_file_size, validate_document_extension])
    uploaded_at = models.DateTimeField(auto_now_add=True)
