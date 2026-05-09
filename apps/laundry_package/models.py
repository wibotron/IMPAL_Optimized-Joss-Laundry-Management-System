from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Q
# Create your models here.
class LaundryPackageManager(models.Manager):
    def active_and_valid(self):
        """logic filter paket aktif & tanggal valid di level database"""
        today = timezone.now().date()
        return self.filter(is_active=True).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=today),
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        )

class LaundryPackage(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nama Paket")
    price_per_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Harga per Kilogram (Rp)"
    )
    estimated_days = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="Estimasi Durasi (hari)" 
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tanggal Mulai Berlaku"
    )
    end_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Tanggal Berakhir Berlaku"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Deskripsi Detail Paket"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Aktif"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    objects = LaundryPackageManager()

    class Meta:
        ordering = ['price_per_kg']
        verbose_name = "Paket Laundry"
        verbose_name_plural = "Paket Laundry"
        indexes = [models.Index(fields=['is_active', 'start_date', 'end_date'])]

    def __str__(self):
        return f"{self.name} - Rp {self.price_per_kg:,.0f}/kg"