from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomerRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, required=True, label='Full Name')
    phone_number = forms.CharField(max_length=15, required=True, label='Phone Number')
    address = forms.CharField(widget=forms.Textarea, required=True, label='Address')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'phone_number', 'address', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})
        self.fields['full_name'].widget.attrs['placeholder'] = 'Full name'
        self.fields['phone_number'].widget.attrs['placeholder'] = '08123456789'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['email'].widget.attrs['placeholder'] = 'email@example.com'
        self.fields['address'].widget.attrs['rows'] = 2

class EmployeeCreateForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True, label='Phone Number')
    address = forms.CharField(widget=forms.Textarea, required=True, label='Address')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'phone_number', 'address', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})