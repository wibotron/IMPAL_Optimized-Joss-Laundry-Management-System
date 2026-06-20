import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
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
    from apps.orders.models import Order, Feedback
    today = timezone.now().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    all_orders = Order.objects.all()
    
    orders_today = all_orders.filter(tanggal_order__date=today).count()
    orders_in_progress = all_orders.exclude(progress_status='DIAMBIL').count()
    orders_done_today = all_orders.filter(progress_status='DIAMBIL', tanggal_update__date=today).count()

    # ═══ TAMBAHAN: Query untuk menampilkan order prioritas dan antrian di template ═══
    urgent_orders = all_orders.filter(
        progress_status__in=['DITERIMA', 'DICUCI']
    ).order_by('tanggal_order')[:5]

    orders_today_list = all_orders.filter(
        tanggal_order__date=today
    ).order_by('tanggal_order')
    # ════════════════════════════════════════════════════════════════════════════════

    # ═══ TAMBAHAN: Variabel lain untuk dashboard karyawan sesuai tampilan UI ═══
    walkin_today = all_orders.filter(customer__isnull=True, tanggal_order__date=today).count()
    active_orders = orders_in_progress
    pending_payment = all_orders.filter(payment_status='UNPAID').count()
    need_update = all_orders.filter(progress_status__in=['DITERIMA', 'DICUCI', 'DIKERINGKAN', 'DISETRIKA']).count()
    pending_feedback = Feedback.objects.filter(reply__isnull=True).count()
    my_orders_this_week = all_orders.filter(tanggal_order__date__gte=start_of_week).count()
    avg_rating = Feedback.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    my_rating = round(avg_rating, 1)
    on_time_rate = int((orders_done_today / orders_today) * 100) if orders_today else 0
    urgent_count = urgent_orders.count()
    # ════════════════════════════════════════════════════════════════════════════════

    context = {
        'user': request.user,
        'orders_today': orders_today,
        'orders_in_progress': orders_in_progress,
        'orders_done_today': orders_done_today,
        'urgent_orders': urgent_orders,
        'orders_today_list': orders_today_list,
        # ─── Data tambahan untuk card / metric dashboard ───
        'walkin_today': walkin_today,
        'active_orders': active_orders,
        'pending_payment': pending_payment,
        'need_update': need_update,
        'pending_feedback': pending_feedback,
        'my_orders_this_week': my_orders_this_week,
        'my_rating': my_rating,
        'on_time_rate': on_time_rate,
        'urgent_count': urgent_count,
        # ───────────────────────────────────────────────
    }
    return render(request, 'accounts/dashboard_karyawan.html', context)

@owner_required
def owner_dashboard(request):
    from apps.orders.models import Order, Feedback
    from apps.laundry_package.models import LaundryPackage

    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    # Order stats
    all_orders = Order.objects.all()
    orders_today = all_orders.filter(tanggal_order__date=today).count()
    orders_month = all_orders.filter(tanggal_order__date__gte=start_of_month).count()
    orders_in_progress = all_orders.exclude(progress_status='DIAMBIL').count()
    orders_done_today = all_orders.filter(progress_status='DIAMBIL', tanggal_update__date=today).count()

    # Financial stats (this month)
    month_orders = all_orders.filter(tanggal_order__date__gte=start_of_month, tanggal_order__date__lte=today)
    total_omset = month_orders.aggregate(total=Sum('total_harga'))['total'] or 0
    cash_received = month_orders.filter(payment_status='PAID').aggregate(total=Sum('total_harga'))['total'] or 0
    piutang = month_orders.filter(payment_status='UNPAID').aggregate(total=Sum('total_harga'))['total'] or 0

    # Counts
    total_karyawan = User.objects.filter(role=User.KARYAWAN).count()
    total_customers = User.objects.filter(role=User.CUSTOMER).count()
    total_packages = LaundryPackage.objects.filter(is_active=True).count()

    # Feedback stats
    feedbacks_month = Feedback.objects.filter(created_at__date__gte=start_of_month)
    feedback_count = feedbacks_month.count()
    critical_feedback_count = feedbacks_month.filter(rating__lte=3).count()

    # Recent orders (5 terbaru)
    recent_orders = all_orders.select_related('paket')[:5]

    context = {
        'user': request.user,
        'orders_today': orders_today,
        'orders_month': orders_month,
        'orders_in_progress': orders_in_progress,
        'orders_done_today': orders_done_today,
        'total_omset': total_omset,
        'cash_received': cash_received,
        'piutang': piutang,
        'total_karyawan': total_karyawan,
        'total_customers': total_customers,
        'total_packages': total_packages,
        'feedback_count': feedback_count,
        'critical_feedback_count': critical_feedback_count,
        'recent_orders': recent_orders,
        'today': today,
    }
    return render(request, 'accounts/dashboard_owner.html', context)

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