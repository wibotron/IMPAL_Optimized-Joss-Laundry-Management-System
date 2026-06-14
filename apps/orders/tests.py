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

class GenerateOrderCodeTest(TestCase):

    def setUp(self):
        self.paket = LaundryPackage.objects.create(
            name="Cuci Reguler",
            price_per_kg=5000,
            estimated_days=2,
        )
        self.today_str = datetime.date.today().strftime('%Y%m%d')

    def test_generate_order_code_first_order(self):
        kode = generate_order_code()
        self.assertEqual(kode, f"JOSS-{self.today_str}-0001")

    def test_generate_order_code_increment(self):
        Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="081234567",
            paket=self.paket,
            berat=2,
            progress_status="DITERIMA",
        )
        kode = generate_order_code()
        self.assertEqual(kode, f"JOSS-{self.today_str}-0002")

    def test_generate_order_code_multiple_orders(self):
        for _ in range(3):
            Order.objects.create(
                nama_customer="Saut Tulus",
                nomor_hp="081234567",
                paket=self.paket,
                berat=2,
                progress_status="DITERIMA",
            )
        kode = generate_order_code()
        self.assertEqual(kode, f"JOSS-{self.today_str}-0004")

class GetWhatsappShareLinkTest(TestCase):

    def test_link_with_leading_zero(self):
        link = get_whatsapp_share_link("081234567890", "Halo")
        self.assertEqual(link, "https://wa.me/6281234567890?text=Halo")

    def test_link_with_plus62_prefix(self):
        link = get_whatsapp_share_link("+6281234567890", "Halo")
        self.assertEqual(link, "https://wa.me/6281234567890?text=Halo")

    def test_link_with_dashes_and_encoded_message(self):
        link = get_whatsapp_share_link("0812-3456-7890", "Tes Pesan")
        self.assertEqual(link, "https://wa.me/6281234567890?text=Tes%20Pesan")

    def test_link_with_invalid_phone(self):
        link = get_whatsapp_share_link("abc", "Halo")
        self.assertEqual(link, "#")

class GetNotificationMsgReceivedTest(TestCase):

    def setUp(self):
        self.paket = LaundryPackage.objects.create(
            name="Cuci Reguler",
            price_per_kg=5000,
            estimated_days=2,
        )
        self.order = Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="081234567890",
            paket=self.paket,
            berat=2,
            progress_status="DITERIMA",
        )

    def test_notification_received_contains_phone_and_kode_nota(self):
        link = get_notification_msg_received(self.order)
        self.assertIn("https://wa.me/6281234567890", link)
        self.assertIn(self.order.kode_nota, link)

class GetNotificationMsgReadyTest(TestCase):

    def setUp(self):
        self.paket = LaundryPackage.objects.create(
            name="Cuci Reguler",
            price_per_kg=5000,
            estimated_days=2,
        )
        self.order = Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="081234567890",
            paket=self.paket,
            berat=2,
            progress_status="SELESAI",
            payment_status="PAID",
        )

    def test_notification_ready_contains_phone_and_kode_nota(self):
        link = get_notification_msg_ready(self.order)
        self.assertIn("https://wa.me/6281234567890", link)
        self.assertIn(self.order.kode_nota, link)

class GenerateNotaPdfTest(TestCase):

    def setUp(self):
        self.paket = LaundryPackage.objects.create(
            name="Cuci Reguler",
            price_per_kg=5000,
            estimated_days=2,
        )
        self.order = Order.objects.create(
            nama_customer="Saut Tulus",
            nomor_hp="081234567890",
            paket=self.paket,
            berat=2,
            progress_status="DITERIMA",
        )

    def test_generate_nota_pdf_creates_file(self):
        try:
            url = generate_nota_pdf(self.order)
        except ImportError:
            self.skipTest("WeasyPrint tidak terinstall di environment ini, test dilewati.")

        self.order.refresh_from_db()
        self.assertTrue(self.order.nota_pdf)
        self.assertIn("nota_", self.order.nota_pdf.name)
        self.assertIn(".pdf", self.order.nota_pdf.name)
        self.assertEqual(url, self.order.nota_pdf.url)

    def tearDown(self):
        if self.order.nota_pdf:
            self.order.nota_pdf.delete(save=False)
