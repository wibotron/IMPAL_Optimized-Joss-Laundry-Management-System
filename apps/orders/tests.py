import datetime
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.orders.services import (
    process_order_claim,
    generate_order_code,
    get_whatsapp_share_link,
    get_notification_msg_received,
    get_notification_msg_ready,
    generate_nota_pdf,
)
from apps.orders.models import Order
from apps.laundry_package.models import LaundryPackage
from apps.accounts.models import User


class ProcessOrderClaimTest(TestCase):

    def setUp(self):
        self.paket = LaundryPackage.objects.create(
            name="Cuci Reguler",
            price_per_kg=5000,
            estimated_days=2,
        )

        self.user = User.objects.create_user(
            username="saut",
            password="password123",
            full_name="Saut Tulus",
            phone_number="081234567890",
            role=User.CUSTOMER,
        )

        order1 = Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="081234567",
            customer=None,
            paket=self.paket,
            berat=2,
            progress_status="DITERIMA",
        )

        order2 = Order.objects.create(
            nama_customer="Budi",
            nomor_hp="081234567",
            customer=None,
            paket=self.paket,
            berat=2,
            progress_status="DITERIMA",
        )
        order2.customer = self.user
        order2.save()

        order3 = Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="082252181567",
            customer=None,
            paket=self.paket,
            berat=2,
            progress_status="DITERIMA",
        )

        order4 = Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="081234567",
            customer=None,
            paket=self.paket,
            berat=2,
            progress_status="DIAMBIL",
        )

        self.kode_nota_1 = order1.kode_nota
        self.kode_nota_2 = order2.kode_nota
        self.kode_nota_3 = order3.kode_nota
        self.kode_nota_4 = order4.kode_nota

    def test_claim_success(self):
        order = process_order_claim(
            user=self.user,
            kode_nota=self.kode_nota_1,
            phone_number="081234567"
        )
        self.assertEqual(order.customer, self.user)

    def test_claim_kode_nota_tidak_ditemukan(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Kode nota tidak ditemukan. Periksa kembali kode Anda."
        ):
            process_order_claim(
                user=self.user,
                kode_nota="KODE-SALAH",
                phone_number="081234567"
            )

    def test_claim_sudah_diklaim_akun_lain(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Nota ini sudah diklaim oleh akun lain. Hubungi karyawan jika ada masalah."
        ):
            process_order_claim(
                user=self.user,
                kode_nota=self.kode_nota_2,
                phone_number="081234567"
            )

    def test_claim_nomor_hp_tidak_cocok(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Nomor HP tidak cocok dengan data nota. Pastikan menggunakan nomor yang terdaftar saat order."
        ):
            process_order_claim(
                user=self.user,
                kode_nota=self.kode_nota_3,
                phone_number="0822521567"
            )

    def test_claim_sudah_diambil(self):
        with self.assertRaisesMessage(
            ValidationError,
            "Pesanan yang sudah diambil tidak dapat diklaim ulang."
        ):
            process_order_claim(
                user=self.user,
                kode_nota=self.kode_nota_4,
                phone_number="081234567"
            )

