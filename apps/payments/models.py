from django.db import models
from django.utils import timezone
from apps.tenants.models import Tenant
from utils.file_uploads import get_payment_screenshot_upload_path, get_property_qrcode_upload_path, get_invoice_upload_path
from utils.validators import validate_file_size, validate_image_extension, validate_pdf_extension

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
        ('PENDING', 'Pending'),
        ('IN_VERIFICATION', 'In Verification'),
        ('SUCCESS', 'Success'),
        ('REJECTED', 'Rejected'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    tenant_due = models.ForeignKey('tenants.TenantDue', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='UPI')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            old_payment = Payment.objects.get(pk=self.pk)
            old_status = old_payment.status
            
        super().save(*args, **kwargs)
        
        # Process distribution when status changes to SUCCESS
        if self.status == 'SUCCESS' and old_status != 'SUCCESS':
            amount_left = self.amount
            
            # 1. Specific Invoice
            if self.invoice:
                approved_payments = self.invoice.payments.filter(status='SUCCESS')
                total_paid = sum(p.amount for p in approved_payments)
                self.invoice.amount_paid = total_paid
                self.invoice.save()
                return

            # 2. Specific Due
            if self.tenant_due:
                self.tenant_due.status = 'CLEARED'
                self.tenant_due.save()
                return

            # 3. Generic Tenant Payment (FIFO)
            if self.tenant:
                # Pay invoices first
                pending_invoices = self.tenant.invoices.filter(status__in=['PENDING', 'PARTIAL']).order_by('created_at')
                for inv in pending_invoices:
                    if amount_left <= 0:
                        break
                    rem = inv.remaining_due
                    if amount_left >= rem:
                        amount_left -= rem
                        inv.amount_paid += rem
                        inv.save()
                    else:
                        inv.amount_paid += amount_left
                        amount_left = 0
                        inv.save()
                        
                # Pay dues
                pending_dues = self.tenant.dues.filter(status__in=['PENDING', 'PARTIAL']).order_by('created_at')
                for due in pending_dues:
                    if amount_left <= 0:
                        break
                    if amount_left >= due.amount:
                        amount_left -= due.amount
                        due.status = 'CLEARED'
                        due.save()

            # Trigger invoice generation
            try:
                from .services.invoice_generator import generate_invoice_for_payment
                generate_invoice_for_payment(self)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to generate invoice for Payment #{self.id}: {str(e)}")

    @property
    def current_tenant(self):
        if self.tenant:
            return self.tenant
        if self.invoice:
            return self.invoice.tenant
        if self.tenant_due:
            return self.tenant_due.tenant
        return None

class PaymentProof(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='proof')
    screenshot = models.ImageField(upload_to=get_payment_screenshot_upload_path, validators=[validate_file_size, validate_image_extension])
    upi_payment_date = models.DateField(help_text='Date when the UPI payment was completed')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey('accounts.CustomUser', null=True, blank=True, on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

class PropertyPaymentSettings(models.Model):
    pg_property = models.OneToOneField('properties.Property', on_delete=models.CASCADE, related_name='payment_settings')
    upi_id = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=100)
    qr_code_image = models.ImageField(upload_to=get_property_qrcode_upload_path, null=True, blank=True, validators=[validate_file_size, validate_image_extension])

class RoomElectricityBill(models.Model):
    pg_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='electricity_bills')
    room = models.ForeignKey('properties.Room', on_delete=models.CASCADE, related_name='electricity_bills')
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2)
    units_used = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_unit = models.DecimalField(max_digits=6, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    split_amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_month = models.DateField()
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_electricity_bills')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EB - {self.room} ({self.billing_month.strftime('%b %Y')})"

class GeneratedInvoice(models.Model):
    INVOICE_TYPE_CHOICES = (
        ('RENT', 'Monthly Rent'),
        ('ELECTRICITY', 'Electricity Bill'),
        ('DEPOSIT', 'Security Deposit'),
        ('OTHER', 'Other'),
    )
    STATUS_CHOICES = (
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='generated_invoices')
    pg_property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='generated_invoices')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='generated_invoice')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='RENT')
    invoice_month = models.DateField()
    invoice_year = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')
    pdf_file = models.FileField(upload_to=get_invoice_upload_path, null=True, blank=True, validators=[validate_file_size, validate_pdf_extension])
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.tenant.user.get_full_name()}"
