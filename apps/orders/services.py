"""
Layanan utilitas untuk modul orders.
Mengatur:
- Generate kode nota unik dengan format JOSS-YYYYMMDD-XXXX
- Generate link WhatsApp resmi (wa.me) dengan pesan otomatis
- Pesan notifikasi untuk diterima dan selesai
- Validasi dan proses klaim pesanan oleh customer
- Generate PDF nota menggunakan WeasyPrint
"""
import datetime
import os
import tempfile
from urllib.parse import quote
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.core.files.base import ContentFile
from .models import Order

def generate_order_code() -> str:
    """
    Menghasilkan kode nota dengan format: JOSS-YYYYMMDD-XXXX
    Contoh: JOSS-20260519-0001
    - YYYYMMDD: tanggal hari ini
    - XXXX: urutan pesanan hari ini (mulai 0001, increment)
    """
    today = datetime.date.today()
    today_str = today.strftime('%Y%m%d')
    count = Order.objects.filter(tanggal_order__date=today).count() + 1
    return f"JOSS-{today_str}-{count:04d}"

def get_whatsapp_share_link(phone_number: str, message: str) -> str:
    """
    Generate link WhatsApp resmi dengan domain wa.me.
    - Membersihkan nomor HP (hanya digit)
    - Mengubah awalan '0' menjadi '62' (format internasional)
    - Melakukan URL encoding terhadap pesan
    """
    phone_digits = ''.join(filter(str.isdigit, phone_number))
    if not phone_digits:
        return "#"
    if phone_digits.startswith('0'):
        phone_digits = '62' + phone_digits[1:]
    encoded_msg = quote(message, safe='')
    return f"https://wa.me/{phone_digits}?text={encoded_msg}"

def get_notification_msg_received(order: Order) -> str:
    """Pesan WhatsApp untuk pemberitahuan pesanan DITERIMA"""
    msg = (
        "*JOSS LAUNDRY NOTIFICATION*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Halo Kak {order.nama_customer},\n"
        "Pesanan laundry Anda telah kami *DITERIMA*!\n\n"
        f"- Kode Nota: {order.kode_nota}\n"
        f"- Berat: {order.berat} Kg\n"
        f"- Total Harga: Rp {order.total_harga:,.0f}\n\n"
        "Yuk pantau status cucianmu lewat aplikasi dengan mengklaim Kode Nota di atas.\n\n"
        "Terima kasih..."
    )
    return get_whatsapp_share_link(order.nomor_hp, msg)

def get_notification_msg_ready(order: Order) -> str:
    """Pesan WhatsApp untuk pemberitahuan pesanan SELESAI"""
    msg = (
        "*JOSS LAUNDRY NOTIFICATION*%0A"
        "━━━━━━━━━━━━━━━━━━━━%0A%0A"
        f"Halo Kak {order.nama_customer},%0A"
        "Kabar baik! Cucian Anda sudah *SELESAI* dan siap diambil.%0A%0A"
        f"- Kode Nota: {order.kode_nota}%0A"
        f"- Total Biaya: Rp {order.total_harga:,.0f}%0A"
        f"- Status Bayar: {order.get_payment_status_display()}%0A%0A"
        "Silakan datang ke outlet untuk pengambilan.%0A%0A"
        "Terima kasih..."
    )
    return get_whatsapp_share_link(order.nomor_hp, msg)

def process_order_claim(user, kode_nota: str, phone_number: str) -> Order:
    """
    Memproses klaim pesanan oleh customer yang sudah login.
    Validasi: kode ada, belum diklaim, nomor HP cocok, status bukan DIAMBIL.
    """
    try:
        order = Order.objects.get(kode_nota=kode_nota)
    except Order.DoesNotExist:
        raise ValidationError("Kode nota tidak ditemukan. Periksa kembali kode Anda.")

    if order.customer is not None:
        raise ValidationError("Nota ini sudah diklaim oleh akun lain. Hubungi karyawan jika ada masalah.")

    if order.nomor_hp != phone_number:
        raise ValidationError("Nomor HP tidak cocok dengan data nota. Pastikan menggunakan nomor yang terdaftar saat order.")

    if order.progress_status == 'DIAMBIL':
        raise ValidationError("Pesanan yang sudah diambil tidak dapat diklaim ulang.")

    order.customer = user
    order.save()
    return order

def generate_nota_pdf(order: Order) -> str:
    """Generate PDF nota laundry menggunakan WeasyPrint dan simpan ke field nota_pdf"""
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise ImportError("WeasyPrint tidak terinstall. Jalankan: pip install weasyprint")

    template = get_template('orders/nota_pdf.html')
    html_string = template.render({'order': order})

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        HTML(string=html_string).write_pdf(
            tmp_file,
            stylesheets=[CSS(string='@page { size: A4; margin: 1.5cm; }')]
        )
        tmp_file_path = tmp_file.name

    with open(tmp_file_path, 'rb') as f:
        filename = f"nota_{order.kode_nota}.pdf"
        order.nota_pdf.save(filename, ContentFile(f.read()), save=True)

    os.unlink(tmp_file_path)
    return order.nota_pdf.url