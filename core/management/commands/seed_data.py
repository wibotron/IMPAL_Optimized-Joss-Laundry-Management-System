from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.laundry_package.models import LaundryPackage

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeding data master: paket laundry, akun owner, dan akun karyawan contoh'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Memulai seeding data master...")

        # ========================
        #     Paket Laundry
        # ========================
        packages = [
            {'name': 'Reguler', 'price_per_kg': 8000, 'estimated_days': 2},
            {'name': 'Express', 'price_per_kg': 12000, 'estimated_days': 1},
            {'name': 'Eksekutif', 'price_per_kg': 15000, 'estimated_days': 1},
        ]

        for pkg in packages:
            obj, created = LaundryPackage.objects.get_or_create(
                name=pkg['name'],
                defaults={
                    'price_per_kg': pkg['price_per_kg'],
                    'estimated_days': pkg['estimated_days'],
                    'is_active': True,
                    # start_date, end_date, description biarkan default (null/blank)
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Paket '{obj.name}' dibuat"))
            else:
                self.stdout.write(f"  ⚠️ Paket '{obj.name}' sudah ada, dilewati")

        # ========================
        #  Akun Owner (superuser)
        # ========================
        owner_data = {
            'username': 'owner',
            'full_name': 'Owner Laundry',
            'phone_number': '081234567890',
            'role': 'owner',
            'is_superuser': True,
            'is_staff': True,
        }
        owner, created = User.objects.get_or_create(
            username=owner_data['username'],
            defaults=owner_data
        )
        if created:
            owner.set_password('owner123')
            owner.save()
            self.stdout.write(self.style.SUCCESS("  ✅ Akun owner dibuat (username: owner, password: owner123)"))
        else:
            self.stdout.write("  ⚠️ Akun owner sudah ada, tidak diubah")

        # ========================
        #   Akun Karyawan Contoh
        # ========================
        karyawan_data = {
            'username': 'kasir',
            'full_name': 'Kasir Laundry',
            'phone_number': '081234567891',
            'role': 'karyawan',
        }
        karyawan, created = User.objects.get_or_create(
            username=karyawan_data['username'],
            defaults=karyawan_data
        )
        if created:
            karyawan.set_password('kasir123')
            karyawan.save()
            self.stdout.write(self.style.SUCCESS("  ✅ Akun karyawan contoh dibuat (username: kasir, password: kasir123)"))
        else:
            self.stdout.write("  ⚠️ Akun karyawan sudah ada, dilewati")

        self.stdout.write(self.style.SUCCESS("🎉 Seeding data master selesai!"))