import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from apps.accounts.decorators import owner_required
from .services import get_all_report_data

@login_required
@owner_required
def dashboard(request):
    today = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = today.replace(day=1)
            end_date = today
    else:
        start_date = today.replace(day=1)
        end_date = today

    # Ambil semua data dari services
    data = get_all_report_data(start_date, end_date)

    # Konversi list ke JSON string agar aman di JavaScript
    data['daily_trend']['dates'] = json.dumps(data['daily_trend']['dates'])
    data['daily_trend']['revenues'] = json.dumps(data['daily_trend']['revenues'])
    data['top_packages']['labels'] = json.dumps(data['top_packages']['labels'])
    data['top_packages']['data'] = json.dumps(data['top_packages']['data'])

    # Hitung persentase untuk progress bar
    total_fb = data['sentiment']['positive'] + data['sentiment']['neutral'] + data['sentiment']['negative']
    data['sentiment']['positive_percentage'] = (data['sentiment']['positive'] / total_fb * 100) if total_fb > 0 else 0

    # Tambahkan start_date & end_date ke context untuk form filter
    data['start_date'] = start_date.isoformat()
    data['end_date'] = end_date.isoformat()

    return render(request, 'reports/dashboard.html', data)