from django import forms
from .models import Payment, Invoice, ElectricityBill, PaymentProof, PropertyPaymentSettings
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

class ElectricityBillForm(forms.ModelForm):
    class Meta:
        model = ElectricityBill
        fields = ['billing_month', 'total_bill_amount']
        widgets = {
            'billing_month': forms.DateInput(attrs={'class': 'input-field mt-1 block w-full', 'type': 'date'}),
            'total_bill_amount': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full', 'step': '0.01'}),
        }

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ['screenshot', 'utr_number']
        widgets = {
            'screenshot': forms.FileInput(attrs={'class': 'input-field mt-1 block w-full', 'accept': 'image/*'}),
            'utr_number': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full', 'placeholder': 'e.g., 123456789012'}),
        }

class PropertyPaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = PropertyPaymentSettings
        fields = ['upi_id', 'account_holder_name', 'qr_code_image']
        widgets = {
            'upi_id': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'qr_code_image': forms.FileInput(attrs={'class': 'input-field mt-1 block w-full', 'accept': 'image/*'}),
        }
