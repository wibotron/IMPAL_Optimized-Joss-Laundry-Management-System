from django.urls import path
from . import views

app_name = 'packages'

urlpatterns = [
    # view daftar paket laundry
    path('', views.package_list, name='package_list'),

    # manage paket laundry
    path('tambah/', views.package_create, name='package_create'),
    path('edit/<int:pk>/', views.package_update, name='package_update'),
    path('hapus/<int:pk>/', views.package_delete, name='package_delete'),
]