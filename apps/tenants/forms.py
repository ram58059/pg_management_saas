from django import forms
from apps.accounts.models import CustomUser
from .models import Tenant, TenantDocument, TenantDue

class TenantUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'input-field mt-1 block w-full', 'id': 'id_password'}))
    
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
    id_proof_file = forms.FileField(
        required=False, 
        widget=forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100'})
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100', 'accept': 'image/*'})
    )

    class Meta:
        model = Tenant
        fields = [
            'pg_property', 'room', 'emergency_contact_name', 'emergency_contact_number',
            'id_proof_type', 'id_proof_number', 'id_proof_file', 'date_of_joining', 'deposit_amount',
            'profile_photo'
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

class TenantDueForm(forms.ModelForm):
    class Meta:
        model = TenantDue
        fields = ['amount', 'reason', 'custom_reason', 'description', 'due_date', 'status']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full', 'step': '0.01'}),
            'reason': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
            'custom_reason': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'description': forms.Textarea(attrs={'class': 'input-field mt-1 block w-full', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'input-field mt-1 block w-full'}),
            'status': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
        }
