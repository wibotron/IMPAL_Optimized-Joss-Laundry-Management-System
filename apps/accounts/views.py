from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomerRegistrationForm, EmployeeCreationForm, EmployeeChangeForm
from .decorators import customer_required, karyawan_required, owner_required
from .models import User
from .forms import LoginForm  # tambahkan di bagian atas

def landing_page(request):
    """Halaman landing"""
    return render(request, 'landing.html')

def register_customer(request):
    """Registrasi hanya untuk customer"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Registrasi berhasil! Selamat datang, {user.full_name}.')
            return redirect('accounts:dashboard')
        else:
            # Kirim error per field
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomerRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """Login untuk semua role"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.full_name}!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Username atau password salah.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Anda telah logout.')
    return redirect('landing')

@login_required
def dashboard_redirect(request):
    """Redirect ke dashboard sesuai role"""
    if request.user.is_customer():
        return redirect('accounts:customer_dashboard')
    elif request.user.is_karyawan():
        return redirect('accounts:karyawan_dashboard')
    elif request.user.is_owner():
        return redirect('accounts:owner_dashboard')
    return redirect('accounts:login')

@customer_required
def customer_dashboard(request):
    return render(request, 'accounts/dashboard_customer.html', {'user': request.user})

@karyawan_required
def karyawan_dashboard(request):
    return render(request, 'accounts/dashboard_karyawan.html', {'user': request.user})

@owner_required
def owner_dashboard(request):
    return render(request, 'accounts/dashboard_owner.html', {'user': request.user})

# ------------------- Manajemen Karyawan (Owner only) -------------------

@owner_required
def karyawan_list(request):
    """Daftar semua karyawan"""
    karyawan = User.objects.filter(role=User.KARYAWAN).order_by('-date_joined')
    return render(request, 'accounts/karyawan_list.html', {'karyawan': karyawan})

@owner_required
def karyawan_create(request):
    """Tambah karyawan baru"""
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            karyawan = form.save()
            messages.success(request, f'Karyawan {karyawan.full_name} berhasil ditambahkan.')
            return redirect('accounts:karyawan_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeCreationForm()
    return render(request, 'accounts/karyawan_form.html', {'form': form, 'title': 'Tambah Karyawan'})

@owner_required
def karyawan_update(request, pk):
    """Edit data karyawan"""
    karyawan = get_object_or_404(User, pk=pk, role=User.KARYAWAN)
    if request.method == 'POST':
        form = EmployeeChangeForm(request.POST, instance=karyawan)
        if form.is_valid():
            karyawan = form.save()
            messages.success(request, f'Data karyawan {karyawan.full_name} berhasil diupdate.')
            return redirect('accounts:karyawan_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EmployeeChangeForm(instance=karyawan)
    return render(request, 'accounts/karyawan_form.html', {'form': form, 'title': 'Edit Karyawan'})

@owner_required
def karyawan_delete(request, pk):
    """Hapus karyawan"""
    karyawan = get_object_or_404(User, pk=pk, role=User.KARYAWAN)
    if request.method == 'POST':
        nama = karyawan.full_name
        karyawan.delete()
        messages.success(request, f'Karyawan {nama} berhasil dihapus.')
        return redirect('accounts:karyawan_list')
    return render(request, 'accounts/karyawan_confirm_delete.html', {'karyawan': karyawan})