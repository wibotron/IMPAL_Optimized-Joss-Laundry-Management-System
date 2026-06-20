from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import datetime
from apps.accounts.decorators import owner_or_karyawan_required, customer_required

from .models import Order, Feedback
from .forms import (
    OrderWalkInForm, ClaimOrderForm, UpdateProgressForm,
    FeedbackForm, ReplyFeedbackForm
)
from .services import (
    get_notification_msg_received, get_notification_msg_ready,
    process_order_claim, generate_nota_pdf
)


# ==================== KARYAWAN / OWNER ====================
@owner_or_karyawan_required
def order_list_karyawan(request):
    orders = Order.objects.select_related('paket', 'customer').prefetch_related('progress_logs').all()

    # Filter tanggal
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            orders = orders.filter(tanggal_order__date__gte=start_date_obj)
        except ValueError:
            pass
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(tanggal_order__date__lte=end_date_obj)
        except ValueError:
            pass

    # Filter search, progress, payment (kode yang sudah ada)
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(Q(kode_nota__icontains=search) | Q(nama_customer__icontains=search))

    progress = request.GET.get('progress', '')
    if progress:
        orders = orders.filter(progress_status=progress)

    payment = request.GET.get('payment', '')
    if payment:
        orders = orders.filter(payment_status=payment)

    wa_link = request.GET.get('wa_link')

    context = {
        'orders': orders,
        'progress_choices': Order.PROGRESS_CHOICES,
        'payment_choices': Order.PAYMENT_CHOICES,
        'selected_progress': progress,
        'selected_payment': payment,
        'search_query': search,
        'wa_link': wa_link,
        'start_date': start_date if start_date else '',
        'end_date': end_date if end_date else '',
    }
    return render(request, 'orders/order_list_karyawan.html', context)


@owner_or_karyawan_required
def order_create_walkin(request):
    """Form input order walk-in customer, langsung generate link WA"""
    if request.method == 'POST':
        form = OrderWalkInForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = None
            order.save()
            wa_link = get_notification_msg_received(order)
            return render(request, 'orders/order_success.html', {'order': order, 'wa_link': wa_link})
    else:
        form = OrderWalkInForm()
    return render(request, 'orders/order_form_karyawan.html', {'form': form})


@owner_or_karyawan_required
def update_progress(request, order_id):
    """Update status progress order. Jika status menjadi SELESAI, siapkan link WA"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = UpdateProgressForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['progress_status']
            order.progress_status = new_status
            order.save()
            if new_status == 'SELESAI':
                wa_link = get_notification_msg_ready(order)
                messages.info(request, 'Status SELESAI. Jangan lupa notifikasi customer via WA.')
                return redirect(f"{request.META.get('HTTP_REFERER', '/')}?wa_link={wa_link}")
            messages.success(request, f'Status berhasil diubah menjadi {order.get_progress_status_display()}')
    return redirect('orders:order_list_karyawan')

@owner_or_karyawan_required
def confirm_payment(request, order_id):
    """Konfirmasi pembayaran customer -> ubah status jadi PAID & DIAMBIL, generate PDF nota"""
    order = get_object_or_404(Order, id=order_id)
    if order.progress_status == 'SELESAI' and order.payment_status == 'UNPAID':
        order.payment_status = 'PAID'
        order.progress_status = 'DIAMBIL'
        order.save()
        try:
            generate_nota_pdf(order)
            messages.success(request, f'Pembayaran {order.kode_nota} dikonfirmasi. Nota PDF siap diunduh.')
        except Exception as e:
            messages.warning(request, f'Pembayaran berhasil, tapi gagal generate PDF: {e}')
    else:
        messages.error(request, 'Order tidak dapat dibayar (status bukan SELESAI atau sudah PAID).')
    return redirect('orders:order_list_karyawan')


@owner_or_karyawan_required
def reply_feedback(request, feedback_id):
    """Halaman untuk karyawan/owner membalas feedback customer"""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    if request.method == 'POST':
        form = ReplyFeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            messages.success(request, 'Balasan feedback disimpan.')
            return redirect('orders:order_list_karyawan')
    else:
        form = ReplyFeedbackForm(instance=feedback)
    return render(request, 'orders/reply_feedback.html', {'form': form, 'feedback': feedback})

@owner_or_karyawan_required
def karyawan_download_nota(request, order_id):
    """Karyawan/owner download PDF nota untuk order yang sudah lunas"""
    order = get_object_or_404(Order, id=order_id)
    if order.payment_status != 'PAID':
        messages.error(request, 'Nota hanya tersedia setelah pembayaran lunas.')
        return redirect('orders:order_list_karyawan')
    if not order.nota_pdf:
        try:
            generate_nota_pdf(order)
        except Exception as e:
            messages.error(request, f'Gagal generate nota: {e}')
            return redirect('orders:order_list_karyawan')
    return redirect(order.nota_pdf.url)

@owner_or_karyawan_required
def regenerate_nota(request, order_id):
    """Generate ulang PDF nota untuk order yang sudah lunas"""
    order = get_object_or_404(Order, id=order_id)
    if order.payment_status != 'PAID':
        messages.error(request, 'Nota hanya bisa digenerate untuk pesanan yang sudah lunas.')
        return redirect('orders:order_list_karyawan')
    
    try:
        generate_nota_pdf(order)
        messages.success(request, f'Nota untuk {order.kode_nota} berhasil digenerate.')
    except Exception as e:
        messages.error(request, f'Gagal generate nota: {str(e)}')
    
    return redirect('orders:order_list_karyawan')

# ==================== CUSTOMER ====================

@login_required
@customer_required
def claim_order(request):
    """Form klaim pesanan menggunakan kode nota dan nomor HP"""
    if request.method == 'POST':
        form = ClaimOrderForm(request.POST)
        if form.is_valid():
            kode = form.cleaned_data['kode_nota']
            hp = form.cleaned_data['nomor_hp']
            try:
                process_order_claim(request.user, kode, hp)
                messages.success(request, 'Pesanan berhasil diklaim!')
                return redirect('orders:customer_dashboard')
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        form = ClaimOrderForm()
    return render(request, 'orders/claim_nota.html', {'form': form})


@login_required
@customer_required
def customer_dashboard(request):
    """Dashboard customer: daftar pesanan yang sudah diklaim, dengan filter"""
    orders = request.user.orders.all().prefetch_related('progress_logs').order_by('-tanggal_order')
    progress = request.GET.get('progress', '')
    payment = request.GET.get('payment', '')
    if progress:
        orders = orders.filter(progress_status=progress)
    if payment:
        orders = orders.filter(payment_status=payment)

    context = {
        'orders': orders,
        'progress_choices': Order.PROGRESS_CHOICES,
        'payment_choices': Order.PAYMENT_CHOICES,
        'selected_progress': progress,
        'selected_payment': payment,
    }
    return render(request, 'orders/customer_dashboard.html', context)

@login_required
@customer_required
def give_feedback(request, order_id):
    """Form memberi feedback untuk pesanan yang sudah lunas"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.payment_status != 'PAID':
        messages.error(request, 'Feedback hanya bisa diberikan setelah pesanan lunas.')
        return redirect('orders:customer_dashboard')
    if hasattr(order, 'feedback'):
        messages.warning(request, 'Anda sudah memberi feedback untuk pesanan ini.')
        return redirect('orders:customer_dashboard')

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.order = order
            feedback.save()
            messages.success(request, 'Terima kasih atas feedback Anda!')
            return redirect('orders:customer_dashboard')
    else:
        form = FeedbackForm()
    return render(request, 'orders/give_feedback.html', {'form': form, 'order': order})


@login_required
@customer_required
def download_nota(request, order_id):
    """Download PDF nota untuk pesanan customer yang sudah lunas"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.payment_status != 'PAID':
        messages.error(request, 'Nota hanya tersedia setelah pembayaran lunas.')
        return redirect('orders:customer_dashboard')
    if not order.nota_pdf:
        try:
            generate_nota_pdf(order)
        except Exception as e:
            messages.error(request, f'Gagal generate nota: {e}')
            return redirect('orders:customer_dashboard')
    return redirect(order.nota_pdf.url)