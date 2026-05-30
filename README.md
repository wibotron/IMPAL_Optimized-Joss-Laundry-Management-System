# JOSS Laundry Management System

Sistem Informasi Manajemen Laundry berbasis web untuk mengelola pesanan, pembayaran, feedback, dan laporan bisnis.  
Dibangun dengan **Django** dan **PostgreSQL** sebagai tugas besar mata kuliah IMPLEMENTASI dan PENGUJIAN PERANGKAT LUNAK.

## Project Structure
```text
IMPAL_Optimized-Joss-Laundry-Management-System/
├── .gitignore
├── apps/
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── decorators.py
│   │   ├── forms.py
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── laundry_package/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── orders/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   └── reports/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── migrations/
│       │   └── __init__.py
│       ├── models.py
│       ├── services.py
│       ├── tests.py
│       ├── urls.py
│       └── views.py
├── core/
│   ├── __init__.py
│   ├── asgi.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── seed_data.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
├── manage.py
├── README.md
├── requirements.txt
└── templates/
    ├── accounts/
    │   ├── dashboard_customer.html
    │   ├── dashboard_karyawan.html
    │   ├── dashboard_owner.html
    │   ├── karyawan_confirm_delete.html
    │   ├── karyawan_form.html
    │   ├── karyawan_list.html
    │   ├── login.html
    │   └── register.html
    ├── base.html
    ├── landing.html
    ├── orders/
    │   ├── claim_nota.html
    │   ├── customer_dashboard.html
    │   ├── give_feedback.html
    │   ├── nota_pdf.html
    │   ├── order_form_karyawan.html
    │   ├── order_list_karyawan.html
    │   ├── order_success.html
    │   └── reply_feedback.html
    ├── packages/
    │   ├── package_confirm_detele.html
    │   ├── package_form.html
    │   └── package_list.html
    └── reports/
        └── dashboard.html
```

## Main Features

- **Multi-role**: Customer, Karyawan, Owner dengan dashboard masing-masing.
- **Manajemen Akun Karyawan**: Dilakukan oleh Owner.
- **Manajemen Paket Laundry**: Owner dapat menambah, mengedit, menghapus paket laundry (dengan periode berlaku).
- **Order Walk-in**: Karyawan input pesanan tanpa login customer, generate kode nota unik, dan kirim notifikasi via WhatsApp.
- **Klaim Pesanan**: Customer dapat mengklaim nota menggunakan kode & nomor HP yang diterima.
- **Update Progress & Pembayaran**: Karyawan mengubah status pencucian (DITERIMA → DICUCI → … → DIAMBIL) dan mengonfirmasi pembayaran.
- **Nota PDF**: Otomatis digenerate saat pembayaran lunas, bisa diunduh oleh customer dan karyawan.
- **Feedback & Balasan**: Customer memberi rating & komentar; karyawan/owner dapat membalas.
- **Laporan Bisnis (Owner)**: 
  - Total omset, uang masuk, piutang.
  - Grafik tren pendapatan harian.
  - Top 5 paket terlaris.
  - Statistik kepuasan pelanggan (rating).
  - Tabel feedback kritik (rating 1-3).
- **Otomatisasi WhatsApp**: Pesan notifikasi diterima & selesai dengan link wa.me.

## Tech Stack

- Backend: Python 3.10+ / Django 4.2
- Database: PostgreSQL
- Frontend: Tailwind CSS + Chart.js
- PDF Generator: WeasyPrint (atau xhtml2pdf sebagai alternatif)
- Lainnya: `psycopg2-binary`, `python-decouple` (opsional)

## How to Run

### Prasyarat

- Python 3.10 atau lebih baru
- PostgreSQL (atau bisa ganti ke SQLite untuk testing cepat)
- Git

### Langkah-langkah

1. **Clone repositori**
   ```bash
   git clone https://github.com/username/IMPAL_Optimized-Joss-Laundry-Management-System.git
   cd IMPAL_Optimized-Joss-Laundry-Management-System
2. **Buat dan aktifkan virtual environment**
   ```bash
   git clone https://github.com/username/IMPAL_Optimized-Joss-Laundry-Management-System.git
   cd IMPAL_Optimized-Joss-Laundry-Management-System
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
4. **Konfigurasi Database**
   - buat database postgreSQL dengan nama bebas.
   - Salin file .env.example berikut menjadi .env dilanjut edit core/settings.py:
   ```bash
   DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'joss_laundry',
            'USER': 'postgres',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
   }
5. **Jalankan Migrasi**
   ``` bash
   python manage.py makemigrations
   python manage.py migrate
6. **Isi data master (SEEDING)**
   WAJIB dijalankan setelah migrasi untuk mengisi data awal, Script ini akan membuat:
   - Paket laundry: Reguler, Express, Eksekutif
   - Akun Owner: owner / owner123
   - Akun Karyawan contoh: kasir / kasir123
   - Script ini aman dijalankan berulang kali (tidak akan menggandakan data).
   ```bash
   python manage.py seed_data
7. Kumpulkan static files (untuk production, opsional di development)
   ```bash
   python manage.py collectstatic
8. **Jalankan Server Development**
   ```bash
   python manage.py runserver
## Kontribusi
1. Fork repositori ini.
2. Buat branch fitur (git checkout -b fitur-anda).
3. Commit perubahan (git commit -m 'Menambahkan fitur X').
4. Push ke branch (git push origin fitur-anda).
5. Buka Pull Request di GitHub.
