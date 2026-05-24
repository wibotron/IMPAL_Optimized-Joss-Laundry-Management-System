from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Landing & autentikasi
    # path('', views.landing_page, name='landing'),
    path('register/', views.register_customer, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # Dashboard per role
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/karyawan/', views.karyawan_dashboard, name='karyawan_dashboard'),
    path('dashboard/owner/', views.owner_dashboard, name='owner_dashboard'),

    # Manajemen karyawan (owner only)
    path('karyawan/', views.karyawan_list, name='karyawan_list'),
    path('karyawan/tambah/', views.karyawan_create, name='karyawan_create'),
    path('karyawan/edit/<int:pk>/', views.karyawan_update, name='karyawan_update'),
    path('karyawan/hapus/<int:pk>/', views.karyawan_delete, name='karyawan_delete'),
]