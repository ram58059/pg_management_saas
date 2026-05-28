import os
import django
from django.core.files import File
from django.conf import settings
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Tenant, TenantDocument
from apps.payments.models import PropertyPaymentSettings, PaymentProof, GeneratedInvoice

def migrate_model_files(model_class, file_field_name):
    print(f"Migrating {model_class.__name__}.{file_field_name} to S3...")
    instances = model_class.objects.exclude(**{f"{file_field_name}": ''})
    
    count = 0
    for instance in instances:
        file_field = getattr(instance, file_field_name)
        if not file_field:
            continue
            
        # Check if file exists locally
        try:
            # If the file is already on S3 (has a URL starting with https://s3), skip or re-upload if we want to enforce new naming
            # For this script, we'll assume we want to re-save everything to enforce the new naming convention and ensure it's on S3.
            
            # Get the actual local path. If it's already on S3, file_field.path might throw NotImplementedError
            try:
                local_path = file_field.path
            except NotImplementedError:
                print(f"  [{instance.id}] File already on remote storage, skipping.")
                continue
                
            if not os.path.exists(local_path):
                print(f"  [{instance.id}] Local file not found: {local_path}")
                continue
                
            # Read local file and re-save. 
            # The field's `upload_to` will automatically generate the new S3 path 
            # and the storage backend (if S3 is configured) will upload it.
            with open(local_path, 'rb') as f:
                django_file = File(f)
                setattr(instance, '_skip_photo_lock', True)
                # This will trigger the new upload_to method and save to S3
                file_field.save(os.path.basename(local_path), django_file, save=True)
                
            print(f"  [{instance.id}] Successfully migrated to: {file_field.name}")
            count += 1
            
        except Exception as e:
            print(f"  [{instance.id}] Error migrating file: {str(e)}")
            
    print(f"Finished migrating {count} files for {model_class.__name__}.\n")

if __name__ == '__main__':
    # Ensure S3 storage is active
    if settings.DEFAULT_FILE_STORAGE != 'storages.backends.s3boto3.S3Boto3Storage':
        print("WARNING: DEFAULT_FILE_STORAGE is not set to S3Boto3Storage.")
        print("Please ensure your .env has AWS keys before running this script.")
        sys.exit(1)
        
    migrate_model_files(Tenant, 'profile_photo')
    migrate_model_files(TenantDocument, 'file')
    migrate_model_files(PropertyPaymentSettings, 'qr_code_image')
    migrate_model_files(PaymentProof, 'screenshot')
    migrate_model_files(GeneratedInvoice, 'pdf_file')
    
    print("All media migration completed successfully.")
