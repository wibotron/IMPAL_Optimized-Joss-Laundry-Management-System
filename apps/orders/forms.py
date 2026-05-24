from django import forms
from django.utils import timezone
from .models import Order, Feedback
from apps.laundry_package.models import LaundryPackage

class OrderWalkInForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['nama_customer', 'nomor_hp', 'paket', 'berat']
        widgets = {
            'nama_customer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap'}),
            'nomor_hp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08123456789'}),
            'paket': forms.Select(attrs={'class': 'form-control'}),
            'berat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Berat dalam kg'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['paket'].queryset = LaundryPackage.objects.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )

class ClaimOrderForm(forms.Form):
    kode_nota = forms.CharField(max_length=20, label='Kode Nota', widget=forms.TextInput(attrs={'class': 'form-control'}))
    nomor_hp = forms.CharField(max_length=15, label='Nomor HP', widget=forms.TextInput(attrs={'class': 'form-control'}))

class UpdateProgressForm(forms.Form):
    progress_status = forms.ChoiceField(choices=Order.PROGRESS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'teks']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}, choices=[(i, i) for i in range(1,6)]),
            'teks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tulis feedback Anda...'}),
        }

class ReplyFeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['reply']
        widgets = {
            'reply': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Balasan karyawan/owner...'})
        }