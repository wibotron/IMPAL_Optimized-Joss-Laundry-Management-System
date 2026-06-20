from django import forms
from .models import LaundryPackage
from django.utils import timezone

class PackageForm(forms.ModelForm):
    class Meta:
        model = LaundryPackage
        fields = [
            'name', 'price_per_kg', 'estimated_days',
            'start_date', 'end_date', 'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        estimated_days = cleaned_data.get('estimated_days')
        is_active = cleaned_data.get('is_active')

        # Validasi: periode berlaku harus cukup untuk estimasi durasi
        if start_date and end_date and estimated_days:
            delta = (end_date - start_date).days
            if delta < estimated_days:
                raise forms.ValidationError(
                    f"Masa berlaku paket ({delta} hari) lebih pendek dari estimasi durasi ({estimated_days} hari). "
                    "Perpanjang masa berlaku atau kurangi estimasi hari."
                )

        # Validasi: jika owner ingin mengaktifkan, pastikan tanggal sekarang dalam rentang
        if is_active:
            today = timezone.now().date()
            if start_date and start_date > today:
                raise forms.ValidationError(
                    f"Tidak dapat mengaktifkan paket karena tanggal mulai ({start_date}) masih akan datang. "
                    "Silakan aktifkan setelah tanggal mulai tercapai."
                )
            if end_date and end_date < today:
                raise forms.ValidationError(
                    f"Tidak dapat mengaktifkan paket karena tanggal berakhir ({end_date}) sudah lewat."
                )
        return cleaned_data
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
        if LaundryPackage.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Nama paket sudah digunakan (tidak peka huruf besar/kecil).")
        return name