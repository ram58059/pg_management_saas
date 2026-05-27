import os
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.payments.models import GeneratedInvoice

def generate_invoice_for_payment(payment):
    # Skip if an invoice is already generated
    if hasattr(payment, 'generated_invoice'):
        return payment.generated_invoice

    tenant = payment.current_tenant
    if not tenant:
        return None

    property_obj = tenant.pg_property

    # Determine invoice type and month
    invoice_type = 'OTHER'
    invoice_month = timezone.now().date()
    invoice_year = invoice_month.year

    if payment.invoice:
        invoice_type = 'RENT'
        invoice_month = payment.invoice.billing_month
        invoice_year = payment.invoice.billing_month.year
    elif payment.tenant_due:
        invoice_type = 'OTHER'  # You can extend this logic later
    else:
        invoice_type = 'DEPOSIT' if payment.amount > 10000 else 'RENT' # fallback

    # Generate Invoice Number: INV-YYYY-MM-XXXX
    month_str = invoice_month.strftime('%m')
    prefix = f"INV-{invoice_year}-{month_str}-"
    last_invoice = GeneratedInvoice.objects.filter(invoice_number__startswith=prefix).order_by('id').last()
    
    if last_invoice:
        try:
            last_seq = int(last_invoice.invoice_number.split('-')[-1])
            seq = last_seq + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
        
    invoice_number = f"{prefix}{seq:04d}"

    # Render HTML
    context = {
        'invoice_number': invoice_number,
        'tenant': tenant,
        'property': property_obj,
        'payment': payment,
        'amount': payment.amount,
        'invoice_type': dict(GeneratedInvoice.INVOICE_TYPE_CHOICES).get(invoice_type, invoice_type),
        'date': timezone.now().date(),
        'month_name': invoice_month.strftime('%B %Y')
    }

    html_string = render_to_string('invoice/pdf_template.html', context)

    # WeasyPrint PDF Generation
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_string).write_pdf()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"WeasyPrint failed: {str(e)}")
        raise e

    # Create GeneratedInvoice
    invoice_obj = GeneratedInvoice(
        invoice_number=invoice_number,
        tenant=tenant,
        pg_property=property_obj,
        payment=payment,
        amount=payment.amount,
        invoice_type=invoice_type,
        invoice_month=invoice_month,
        invoice_year=invoice_year,
        status='PAID'
    )
    
    # Save the file. Django's FileField will handle S3 upload automatically.
    # filename format: tenantname_invoice_month_year_timestamp.pdf
    filename = f"{tenant.user.first_name.lower()}_invoice_{invoice_month.strftime('%b').lower()}_{invoice_year}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    invoice_obj.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
    invoice_obj.save()
    
    return invoice_obj
