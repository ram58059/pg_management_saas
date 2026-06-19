from django import forms
from .models import Payment, Invoice, PaymentProof, PropertyPaymentSettings
from apps.properties.models import Property

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'transaction_id', 'payment_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
            'transaction_id': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'input-field mt-1 block w-full'}),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['tenant', 'billing_month', 'rent_amount', 'due_date']
        widgets = {
            'tenant': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
            'billing_month': forms.DateInput(attrs={'type': 'date', 'class': 'input-field mt-1 block w-full'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'input-field mt-1 block w-full'}),
        }



class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ['screenshot', 'upi_payment_date']
        labels = {
            'upi_payment_date': 'UPI Payment Date',
        }
        widgets = {
            'screenshot': forms.FileInput(attrs={'class': 'input-field mt-1 block w-full', 'accept': 'image/jpeg,image/png,image/webp'}),
            'upi_payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input-field mt-1 block w-full',
            }),
        }

    def clean_upi_payment_date(self):
        upi_payment_date = self.cleaned_data.get('upi_payment_date')
        if not upi_payment_date:
            raise forms.ValidationError('Please enter the date when you completed the UPI payment.')
        return upi_payment_date

    def clean_screenshot(self):
        screenshot = self.cleaned_data.get('screenshot')
        if not screenshot:
            return screenshot
            
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if screenshot.size > max_size:
            raise forms.ValidationError("File size must be under 5MB.")
            
        # Validate file type
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        import os
        ext = os.path.splitext(screenshot.name)[1].lower()
        if ext not in valid_extensions:
            raise forms.ValidationError("Unsupported file extension. Allowed extensions are: jpg, jpeg, png, webp.")
            
        # You could also use python-magic or django's built-in tools to validate mimetype
        # if more robust security is needed against spoofed extensions.
        
        return screenshot

class PropertyPaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = PropertyPaymentSettings
        fields = ['upi_id', 'account_holder_name', 'qr_code_image']
        widgets = {
            'upi_id': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'qr_code_image': forms.FileInput(attrs={'class': 'input-field mt-1 block w-full', 'accept': 'image/*'}),
        }
