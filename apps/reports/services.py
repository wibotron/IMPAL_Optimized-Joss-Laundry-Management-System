from django.db.models import Sum, Count, Avg
from django.db import connection
from apps.orders.models import Order, Feedback
from datetime import date

def get_financial_stats(start_date: date, end_date: date):
    orders = Order.objects.filter(tanggal_order__date__gte=start_date, tanggal_order__date__lte=end_date)
    total_omset = orders.aggregate(total=Sum('total_harga'))['total'] or 0
    cash_received = orders.filter(payment_status='PAID').aggregate(total=Sum('total_harga'))['total'] or 0
    piutang = orders.filter(payment_status='UNPAID').exclude(progress_status='DIAMBIL').aggregate(total=Sum('total_harga'))['total'] or 0
    return {'total_omset': total_omset, 'cash_received': cash_received, 'piutang': piutang}

def get_daily_revenue_trend(start_date: date, end_date: date):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DATE(tanggal_order) as date, COALESCE(SUM(total_harga), 0) as revenue
            FROM orders_order
            WHERE payment_status = 'PAID' AND tanggal_order::date BETWEEN %s AND %s
            GROUP BY DATE(tanggal_order)
            ORDER BY date ASC
        """, [start_date, end_date])
        rows = cursor.fetchall()
    dates = [row[0].strftime('%Y-%m-%d') for row in rows]
    revenues = [float(row[1]) for row in rows]
    return {'dates': dates, 'revenues': revenues}

def get_top_packages(start_date: date, end_date: date):
    top = Order.objects.filter(tanggal_order__date__gte=start_date, tanggal_order__date__lte=end_date
    ).values('paket__name').annotate(count=Count('id')).order_by('-count')[:5]
    labels = [item['paket__name'] for item in top]
    data = [item['count'] for item in top]
    return {'labels': labels, 'data': data}

def get_sentiment_stats(start_date: date, end_date: date):
    fb = Feedback.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    avg_rating = fb.aggregate(avg=Avg('rating'))['avg'] or 0
    positive = fb.filter(rating__gte=4).count()
    neutral = fb.filter(rating=3).count()
    negative = fb.filter(rating__lte=2).count()
    return {'avg_rating': round(avg_rating, 2), 'positive': positive, 'neutral': neutral, 'negative': negative}

def get_critical_feedbacks(start_date: date, end_date: date, limit=10):
    feedbacks = Feedback.objects.filter(rating__lte=3, created_at__date__gte=start_date, created_at__date__lte=end_date
    ).select_related('order').order_by('-created_at')[:limit]
    result = []
    for fb in feedbacks:
        result.append({
            'kode_nota': fb.order.kode_nota,
            'nama_customer': fb.order.nama_customer,
            'rating': fb.rating,
            'teks': fb.teks,
            'progress_status': fb.order.get_progress_status_display(),
        })
    return result

def get_all_report_data(start_date: date, end_date: date):
    return {
        'financial': get_financial_stats(start_date, end_date),
        'daily_trend': get_daily_revenue_trend(start_date, end_date),
        'top_packages': get_top_packages(start_date, end_date),
        'sentiment': get_sentiment_stats(start_date, end_date),
        'critical_feedbacks': get_critical_feedbacks(start_date, end_date),
    }