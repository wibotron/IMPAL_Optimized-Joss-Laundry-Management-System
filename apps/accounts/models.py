from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

class User(AbstractUser):
    CUSTOMER = 'customer'
    KARYAWAN = 'karyawan'
    OWNER = 'owner'

    ROLE_CHOICES = (
        (CUSTOMER, 'Customer'),
        (KARYAWAN, 'Karyawan'),
        (OWNER, 'Owner'),
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default=CUSTOMER,
        verbose_name="Peran User"
    )

    full_name = models.CharField(
        max_length=255, 
        verbose_name="Nama Lengkap"
    )

    phone_regex = RegexValidator(
        regex=r'^(?:\+62|0)8[1-9][0-9]{8,11}$',
        message="Nomor telepon harus format Indonesia murni angka (contoh: 08123456789 atau +628123456789)."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=20, 
        unique=True,
        verbose_name="Nomor Telepon"
    )

    address = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Alamat Lengkap"
    )

    def is_customer(self):
        return self.role == self.CUSTOMER

    def is_karyawan(self):
        return self.role == self.KARYAWAN

    def is_owner(self):
        return self.role == self.OWNER
    
    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = self.phone_number.replace(" ", "").replace("-", "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


@receiver(post_save, sender=User)
def set_owner_for_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser and instance.role == User.CUSTOMER:
        instance.role = User.OWNER
        instance.save(update_fields=['role'])