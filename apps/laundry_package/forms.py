from django import forms
from .models import LaundryPackage

class PackageForm(forms.ModelForm):
    class Meta:
        model = LaundryPackage
        fields = [
            'name', 'price_per_kg', 'estimated_days',
            'start_date', 'end_date', 'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_date(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Tanggal mulai tidak boleh lebih besar dari tanggal berakhir.")
        return cleaned_data
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if LaundryPackage.objects.filter(name=name).exists():
            if self.instance.pk and self.instance.name == name:
                return name
            raise forms.ValidationError("Nama paket sudah digunakan.")
        return name