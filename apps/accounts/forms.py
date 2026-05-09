from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User
import re

# ------------------------------------------------------------
#               Form Registrasi Customer
# ------------------------------------------------------------
class CustomerRegistrationForm(UserCreationForm):
    """
    Form registrasi khusus untuk customer.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'phone_number', 'address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})
        self.fields['full_name'].widget.attrs['placeholder'] = 'Contoh: Achmad Wibowo'
        self.fields['phone_number'].widget.attrs['placeholder'] = '08123456789'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['address'].widget.attrs['rows'] = 2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username sudah digunakan.")
        return username

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Nomor telepon sudah terdaftar.")
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if len(password) < 8:
            raise ValidationError("Password minimal harus 8 karakter.")
        if not re.search(r'\d', password):
            raise ValidationError("Password harus mengandung setidaknya satu angka.")
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("Password harus mengandung setidaknya satu huruf.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.CUSTOMER
        if commit:
            user.save()
        return user


# ------------------------------------------------------------
#                      Form Login
# ------------------------------------------------------------
class LoginForm(AuthenticationForm):
    """
    Form login untuk semua actor (customer, karyawan, owner).
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan Password'
        })
    )


# ------------------------------------------------------------
#           Form untuk Menambah Karyawan oleh Owner
# ------------------------------------------------------------
class EmployeeCreationForm(UserCreationForm):
    """
    Form untuk owner MENAMBAHKAN karyawan baru.
    Mengharuskan input password.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'phone_number', 'address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username sudah digunakan.")
        return username

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("Nomor telepon sudah terdaftar.")
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if len(password) < 8:
            raise ValidationError("Password minimal harus 8 karakter.")
        if not re.search(r'\d', password):
            raise ValidationError("Password harus mengandung setidaknya satu angka.")
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("Password harus mengandung setidaknya satu huruf.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.KARYAWAN
        if commit:
            user.save()
        return user


# ------------------------------------------------------------
#           Form untuk Mengedit Karyawan oleh Owner
# ------------------------------------------------------------
class EmployeeChangeForm(UserChangeForm):
    """
    Form untuk owner MENGEDIT data karyawan.
    Field password disembunyikan agar edit tidak mewajibkan ganti password.
    """
    password = None

    class Meta:
        model = User
        fields = ('username', 'full_name', 'phone_number', 'address', 'is_active') 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Checkbox is_active tidak perlu class form-control
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Username sudah digunakan.")
        return username

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Nomor telepon sudah terdaftar.")
        return phone