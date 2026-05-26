from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', _('PG Owner')
        TENANT = 'TENANT', _('Tenant')
        ADMIN = 'ADMIN', _('Admin')
        
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.TENANT)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def is_owner(self):
        return self.role == self.Role.OWNER or self.is_superuser
        
    def is_tenant(self):
        return self.role == self.Role.TENANT

class PGOwner(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='pg_owner_profile')
    company_name = models.CharField(max_length=100)
    gst_number = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return self.company_name
