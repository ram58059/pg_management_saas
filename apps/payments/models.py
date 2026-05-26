from django.db import models
from apps.tenants.models import Tenant

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial Payment'),
        ('PAID', 'Paid'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invoices')
    billing_month = models.DateField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    electricity_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.tenant.user.get_full_name()} ({self.billing_month.strftime('%b %Y')})"

    @property
    def remaining_due(self):
        return self.total_amount - self.amount_paid

    def save(self, *args, **kwargs):
        self.total_amount = self.rent_amount + self.electricity_amount
        if self.amount_paid >= self.total_amount:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        else:
            self.status = 'PENDING'
        super().save(*args, **kwargs)

class Payment(models.Model):
    METHOD_CHOICES = (
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
        ('BANK', 'Bank Transfer'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending Submission'),
        ('SCREENSHOT_UPLOADED', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Only APPROVED payments count towards the invoice amount_paid
        approved_payments = self.invoice.payments.filter(status='APPROVED')
        total_paid = sum(p.amount for p in approved_payments)
        
        self.invoice.amount_paid = total_paid
        self.invoice.save()

class PaymentProof(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='proof')
    screenshot = models.ImageField(upload_to='payment_proofs/')
    utr_number = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey('accounts.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)

class PropertyPaymentSettings(models.Model):
    pg_property = models.OneToOneField('properties.Property', on_delete=models.CASCADE, related_name='payment_settings')
    upi_id = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=100)
    qr_code_image = models.ImageField(upload_to='upi_qr_codes/', null=True, blank=True)

class ElectricityBill(models.Model):
    pg_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='electricity_bills')
    billing_month = models.DateField()
    total_bill_amount = models.DecimalField(max_digits=10, decimal_places=2)
    per_tenant_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
