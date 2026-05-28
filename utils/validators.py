import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_size(value):
    filesize = value.size
    
    if filesize > 5 * 1024 * 1024:
        raise ValidationError(_("The maximum file size that can be uploaded is 5MB"))
    else:
        return value

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Unsupported file extension. Allowed extensions are: .jpg, .jpeg, .png, .webp'))

def validate_document_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Unsupported file extension. Allowed extensions are: .pdf, .jpg, .jpeg, .png'))

def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(_('Unsupported file extension. Only .pdf files are allowed.'))
