from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def is_customer(user):
    return user.is_authenticated and user.is_customer()

def is_karyawan(user):
    return user.is_authenticated and user.is_karyawan()

def is_owner(user):
    return user.is_authenticated and user.is_owner()

# Redirect to dashboard if role check fails
customer_required = user_passes_test(is_customer, login_url='dashboard')
karyawan_required = user_passes_test(is_karyawan, login_url='dashboard')
owner_required = user_passes_test(is_owner, login_url='dashboard')

# Optional: raise 403 Forbidden instead of redirect (more strict)
def owner_required_403(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_owner():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper