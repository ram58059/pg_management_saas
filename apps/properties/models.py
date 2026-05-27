from django.db import models
from apps.accounts.models import PGOwner

class Property(models.Model):
    GENDER_CHOICES = (
        ('MALE', 'Men\'s PG'),
        ('FEMALE', 'Women\'s PG'),
        ('UNISEX', 'Unisex PG'),
    )

    owner = models.ForeignKey(PGOwner, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=200)
    address = models.TextField()
    pg_type = models.CharField(max_length=10, choices=GENDER_CHOICES)
    electricity_cost_per_unit = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Cost per unit in ₹")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_pg_type_display()})"
        
    class Meta:
        verbose_name_plural = 'Properties'

class Room(models.Model):
    pg_property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    capacity = models.PositiveIntegerField(help_text="Number of beds (e.g. 2, 3, 4)")
    is_ac = models.BooleanField(default=False)
    base_rent = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base rent per bed")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.pg_property.name}"
        
    @property
    def occupied_beds(self):
        return self.tenants.filter(is_active=True).count()
        
    @property
    def available_beds(self):
        return self.capacity - self.occupied_beds
