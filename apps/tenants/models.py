from django.db import models
from apps.accounts.models import CustomUser, PGOwner
from apps.properties.models import Property, Room

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
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.room}"

class TenantDocument(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50)
    file = models.FileField(upload_to='tenant_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
