# Create your models here.
import datetime
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator
from apps.laundry_package.models import LaundryPackage
from .middleware import get_current_user
from datetime import timedelta
from django.utils import timezone

class Order(models.Model):
    PROGRESS_CHOICES = [
        ('DITERIMA', 'Diterima'),
        ('DICUCI', 'Dicuci'),
        ('DIKERINGKAN', 'Dikeringkan'),
        ('DISETRIKA', 'Disetrika'),
        ('SELESAI', 'Selesai'),
        ('DIAMBIL', 'Diambil'),
    ]
    PAYMENT_CHOICES = [
        ('UNPAID', 'Belum Bayar'),
        ('PAID', 'Sudah Bayar'),
    ]

    kode_nota = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    nama_customer = models.CharField(max_length=100, help_text="Nama walk-in customer")
    nomor_hp = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^(?:\+62|0)8[1-9][0-9]{8,11}$',
            message="Nomor telepon harus format Indonesia murni angka (contoh: 08123456789 atau +628123456789)."
        )],
        help_text="Nomor HP customer (format Indonesia)"
    )
    paket = models.ForeignKey(LaundryPackage, on_delete=models.PROTECT)
    berat = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    total_harga = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    progress_status = models.CharField(max_length=20, choices=PROGRESS_CHOICES, default='DITERIMA')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='UNPAID')
    tanggal_order = models.DateTimeField(auto_now_add=True)
    tanggal_update = models.DateTimeField(auto_now=True)
    nota_pdf = models.FileField(upload_to='nota/', null=True, blank=True)

    class Meta:
        ordering = ['-tanggal_order']
        indexes = [
            models.Index(fields=['kode_nota']),
            models.Index(fields=['progress_status', 'payment_status']),
        ]

    def generate_kode_nota(self):
        """Delegasi ke service untuk menghasilkan format JOSS-YYYYMMDD-XXXX"""
        from .services import generate_order_code
        return generate_order_code()

    def save(self, *args, **kwargs):
        # Bersihkan nomor hp
        if self.nomor_hp:
            self.nomor_hp = self.nomor_hp.replace(" ", "").replace("-", "")

        # Deteksi perubahan status (hanya jika instance sudah ada di db)
        if self.pk:
            try:
                old = Order.objects.get(pk=self.pk)
                if old.progress_status != self.progress_status:
                    user = get_current_user()
                    ProgressLog.objects.create(
                        order=self,
                        status=self.progress_status,
                        changed_by=user
                    )
            except Order.DoesNotExist:
                pass

        if not self.kode_nota:
            self.kode_nota = self.generate_kode_nota()
            
        if self.progress_status == 'DIAMBIL':
            self.payment_status = 'PAID'
            
        if self.pk is None:
            self.total_harga = self.berat * self.paket.price_per_kg
        else:
            old_data = Order.objects.filter(pk=self.pk).values('berat', 'paket_id').first()
            if old_data and (old_data['berat'] != self.berat or old_data['paket_id'] != self.paket_id):
                self.total_harga = self.berat * self.paket.price_per_kg
                
        super().save(*args, **kwargs)

    def estimated_completion_date(self):
        """Menghitung perkiraan tanggal selesai berdasarkan status dan estimasi paket"""
        if self.progress_status in ['SELESAI', 'DIAMBIL']:
            # Jika sudah selesai/diambil, gunakan tanggal update terakhir
            return self.tanggal_update.date()
        # Jika masih dalam proses, gunakan tanggal order + estimasi hari paket
        return self.tanggal_order.date() + timedelta(days=self.paket.estimated_days)

    def days_remaining(self):
        """Menghitung sisa hari hingga perkiraan selesai"""
        if self.progress_status in ['SELESAI', 'DIAMBIL']:
            return 0
        today = timezone.now().date()
        delta = (self.estimated_completion_date() - today).days
        return max(delta, 0)  # tidak negatif

    def __str__(self):
        return f"{self.kode_nota} - {self.nama_customer}"


class Feedback(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    teks = models.TextField()
    reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback {self.order.kode_nota} - rating {self.rating}"

class ProgressLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='progress_logs')
    status = models.CharField(max_length=20, choices=Order.PROGRESS_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['changed_at']
        verbose_name = "Log Perubahan Status"
        verbose_name_plural = "Log Perubahan Status"

    def __str__(self):
        return f"{self.order.kode_nota} - {self.get_status_display()} pada {self.changed_at.strftime('%d/%m/%Y %H:%M')}"