from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Karyawan/Owner
    path('karyawan/orders/', views.order_list_karyawan, name='order_list_karyawan'),
    path('karyawan/orders/create/', views.order_create_walkin, name='order_create_walkin'),
    path('karyawan/orders/update-progress/<int:order_id>/', views.update_progress, name='update_progress'),
    path('karyawan/orders/confirm-payment/<int:order_id>/', views.confirm_payment, name='confirm_payment'),
    path('karyawan/feedback/reply/<int:feedback_id>/', views.reply_feedback, name='reply_feedback'),
    path('karyawan/orders/download-nota/<int:order_id>/', views.karyawan_download_nota, name='karyawan_download_nota'),
    path('karyawan/orders/regenerate-nota/<int:order_id>/', views.regenerate_nota, name='regenerate_nota'),
    
    # Customer
    path('customer/claim/', views.claim_order, name='claim_order'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/feedback/<int:order_id>/', views.give_feedback, name='give_feedback'),
    path('customer/download-nota/<int:order_id>/', views.download_nota, name='download_nota'),
]