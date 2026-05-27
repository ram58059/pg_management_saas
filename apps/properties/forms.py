from django import forms
from .models import Property, Room

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'pg_type', 'electricity_cost_per_unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full', 'placeholder': 'Property Name'}),
            'address': forms.Textarea(attrs={'class': 'input-field mt-1 block w-full', 'rows': 3, 'placeholder': 'Full Address'}),
            'pg_type': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
            'electricity_cost_per_unit': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full', 'step': '0.01'}),
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['pg_property', 'room_number', 'capacity', 'is_ac', 'base_rent']
        widgets = {
            'pg_property': forms.Select(attrs={'class': 'input-field mt-1 block w-full'}),
            'room_number': forms.TextInput(attrs={'class': 'input-field mt-1 block w-full'}),
            'capacity': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full', 'min': 1}),
            'base_rent': forms.NumberInput(attrs={'class': 'input-field mt-1 block w-full', 'step': '0.01'}),
        }
    
    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pg_property'].queryset = Property.objects.filter(owner=owner)
