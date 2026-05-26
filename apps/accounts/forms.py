from django import forms
from django.contrib.auth.forms import AuthenticationForm

class OwnerLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input-field mt-1 block w-full',
        'placeholder': 'Owner Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'input-field mt-1 block w-full',
        'placeholder': 'Password'
    }))

class TenantLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'input-field mt-1 block w-full',
        'placeholder': 'Tenant Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'input-field mt-1 block w-full',
        'placeholder': 'Password'
    }))
