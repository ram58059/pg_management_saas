import os
import time
import uuid
from datetime import datetime
from django.utils.text import slugify

def generate_safe_filename(parts, ext):
    """
    Centralized helper to generate a safe, collision-free filename.
    `parts` is a list of strings (e.g. ['padur-girls', 'room203', 'priya', '482']).
    `ext` is the file extension (e.g. 'jpg', 'pdf').
    """
    # 1. Clean extension
    ext = ext.lstrip('.').lower()
    
    # 2. Slugify each part and remove empty strings
    clean_parts = []
    for part in parts:
        if part:
            slug = slugify(str(part))
            if slug:
                clean_parts.append(slug)
    
    # 3. Generate timestamp YYYYMMDD_HHMMSS
    now = datetime.now()
    timestamp_str = now.strftime('%Y%m%d_%H%M%S')
    
    # 4. Join parts with underscore
    base_name = "_".join(clean_parts)
    
    # 5. Final filename: basename_timestamp.ext
    # Fallback to a uuid if basename is completely empty
    if not base_name:
        base_name = str(uuid.uuid4())[:8]
        
    final_filename = f"{base_name}_{timestamp_str}.{ext}"
    
    return final_filename, now

def get_payment_screenshot_upload_path(instance, filename):
    """
    Format: payment_screenshots/YYYY/MM/propertyname_roomnumber_tenantname_paymentid_timestamp.ext
    Example: padur-girls_room203_priya_482_20260527_183045.jpg
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    payment = getattr(instance, 'payment', None)
    
    tenant = None
    if payment:
        tenant = payment.tenant
        if not tenant:
            if payment.invoice:
                tenant = payment.invoice.tenant
            elif payment.tenant_due:
                tenant = payment.tenant_due.tenant
                
    property_name = tenant.pg_property.name if tenant and tenant.pg_property else "unknown-property"
    room_number = f"room{tenant.room.room_number}" if tenant and tenant.room else "unknown-room"
    tenant_name = tenant.user.get_full_name() if tenant else "unknown-tenant"
    payment_id = str(payment.id) if payment and payment.id else str(int(time.time()))
    
    parts = [property_name, room_number, tenant_name, payment_id]
    
    new_filename, now = generate_safe_filename(parts, ext)
    folder_path = os.path.join('payment_screenshots', now.strftime('%Y'), now.strftime('%m'))
    
    return os.path.join(folder_path, new_filename)

def get_tenant_document_upload_path(instance, filename):
    """
    Format: tenant_documents/YYYY/MM/propertyname_tenantname_doctype_timestamp.ext
    Example: thoraipakkam_arun_aadhaar_20260527_183045.pdf
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    tenant = getattr(instance, 'tenant', None)
    document_type = getattr(instance, 'document_type', 'document')
    
    property_name = tenant.pg_property.name if tenant and tenant.pg_property else "unknown-property"
    tenant_name = tenant.user.get_full_name() if tenant else "unknown-tenant"
    
    parts = [property_name, tenant_name, document_type]
    
    new_filename, now = generate_safe_filename(parts, ext)
    folder_path = os.path.join('tenant_documents', now.strftime('%Y'), now.strftime('%m'))
    
    return os.path.join(folder_path, new_filename)

def get_agreement_upload_path(instance, filename):
    """
    Format: agreements/YYYY/MM/propertyname_tenantname_agreement_timestamp.ext
    Example: padur-boys_karthik_agreement_20260527_183045.pdf
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    tenant = getattr(instance, 'tenant', None)
    
    property_name = tenant.pg_property.name if tenant and tenant.pg_property else "unknown-property"
    tenant_name = tenant.user.get_full_name() if tenant else "unknown-tenant"
    
    parts = [property_name, tenant_name, 'agreement']
    
    new_filename, now = generate_safe_filename(parts, ext)
    folder_path = os.path.join('agreements', now.strftime('%Y'), now.strftime('%m'))
    
    return os.path.join(folder_path, new_filename)

def get_receipt_upload_path(instance, filename):
    """
    Format: receipts/YYYY/MM/tenantname_receipt_month_year_timestamp.pdf
    Example: priya_receipt_may_2026_20260527_183045.pdf
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    tenant = getattr(instance, 'tenant', None)
    tenant_name = tenant.user.get_full_name() if tenant else "unknown-tenant"
    
    # Try to extract billing month/year if instance has a billing_month DateField
    billing_month = getattr(instance, 'billing_month', None)
    if billing_month:
        month_str = billing_month.strftime('%b') # e.g. may
        year_str = billing_month.strftime('%Y')  # e.g. 2026
    else:
        now = datetime.now()
        month_str = now.strftime('%b')
        year_str = now.strftime('%Y')
        
    parts = [tenant_name, 'receipt', month_str, year_str]
    
    new_filename, now = generate_safe_filename(parts, ext)
    folder_path = os.path.join('receipts', now.strftime('%Y'), now.strftime('%m'))
    
    return os.path.join(folder_path, new_filename)

def get_tenant_photo_upload_path(instance, filename):
    """
    Format: tenant_photos/YYYY/MM/propertyname_roomnumber_tenantname_profile_timestamp.ext
    Example: padur-girls_room203_priya_profile_20260527_183045.jpg
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    property_name = instance.pg_property.name if instance.pg_property else "unknown-property"
    room_number = f"room{instance.room.room_number}" if instance.room else "unknown-room"
    tenant_name = instance.user.get_full_name() if getattr(instance, 'user', None) else "unknown-tenant"
    
    parts = [property_name, room_number, tenant_name, 'profile']
    
    new_filename, now = generate_safe_filename(parts, ext)
    folder_path = os.path.join('tenant_photos', now.strftime('%Y'), now.strftime('%m'))
    
    return os.path.join(folder_path, new_filename)
