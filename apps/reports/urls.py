from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('export/excel/', views.export_orders_excel, name='export_excel'),  # tambahkan ini
]