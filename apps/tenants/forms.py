from django import forms
from apps.accounts.models import CustomUser
from .models import Tenant, TenantDocument

class TenantUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field mt-1 block w-full'}))
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'username': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'email': forms.EmailInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'phone_number': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
        }

class TenantProfileForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            'pg_property', 'room', 'emergency_contact_name', 'emergency_contact_number',
            'id_proof_type', 'id_proof_number', 'date_of_joining', 'deposit_amount'
        ]
        widgets = {
            'pg_property': forms.Select(attrs={'class': 'input-field mt-1 block w-full', 'id': 'id_pg_property'}),
            'room': forms.Select(attrs={'class': 'input-field mt-1 block w-full', 'id': 'id_room'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'id_proof_type': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
            'id_proof_number': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'date_of_joining': forms.DateInput(attrs={'type': 'date', 'class': 'input-field mt-1 block w-full'}),
            'deposit_amount': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full'}),
        }
