from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

def role_required(allowed_roles=[]):
    """
    Decorator untuk membatasi akses berdasarkan role.
    allowed_roles: list of string ['owner', 'karyawan', 'customer']
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Silakan login terlebih dahulu.')
                return redirect(reverse('accounts:login'))
            if request.user.role not in allowed_roles:
                messages.error(request, 'Anda tidak memiliki izin untuk mengakses halaman ini.')
                # Redirect ke dashboard yang sesuai atau landing
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def owner_required(view_func):
    return role_required(['owner'])(view_func)

def karyawan_required(view_func):
    return role_required(['karyawan', 'owner'])(view_func)

def customer_required(view_func):
    return role_required(['customer'])(view_func)

def owner_or_karyawan_required(view_func):
    return role_required(['owner', 'karyawan'])(view_func)