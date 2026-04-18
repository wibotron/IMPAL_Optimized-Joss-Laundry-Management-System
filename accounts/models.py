from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('karyawan', 'Karyawan'),
        ('owner', 'Owner'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def is_customer(self):
        return self.role == 'customer'

    def is_karyawan(self):
        return self.role == 'karyawan'

    def is_owner(self):
        return self.role == 'owner'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# Auto-set superuser role to 'owner'
@receiver(post_save, sender=User)
def set_owner_for_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser and instance.role == 'customer':
        instance.role = 'owner'
        instance.save()