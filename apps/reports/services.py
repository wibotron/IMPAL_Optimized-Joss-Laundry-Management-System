from django.db.models import Sum, Count, Avg
from django.db import connection
from apps.orders.models import Order, Feedback
from datetime import date
import re
import base64
import io
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from django.core.cache import cache

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

def get_export_orders_data(start_date, end_date):
    from apps.orders.models import Order
    
    orders = Order.objects.filter(
        tanggal_order__date__gte=start_date,
        tanggal_order__date__lte=end_date
    ).select_related('paket').prefetch_related('progress_logs')
    
    data = []
    for order in orders:
        logs = {log.status: log.changed_at.strftime("%d/%m/%Y %H:%M") for log in order.progress_logs.all()}
        data.append({
            'kode_nota': order.kode_nota,
            'nama_customer': order.nama_customer,
            'nomor_hp': order.nomor_hp,
            'paket': order.paket.name,
            'berat': float(order.berat),
            'total_harga': float(order.total_harga),
            'progress_status': order.get_progress_status_display(),
            'payment_status': order.get_payment_status_display(),
            'tanggal_order': order.tanggal_order.strftime("%d/%m/%Y %H:%M"),
            'tanggal_update': order.tanggal_update.strftime("%d/%m/%Y %H:%M"),
            'waktu_dicuci': logs.get('DICUCI', ''),
            'waktu_dikeringkan': logs.get('DIKERINGKAN', ''),
            'waktu_disetrika': logs.get('DISETRIKA', ''),
            'waktu_selesai': logs.get('SELESAI', ''),
            'waktu_diambil': logs.get('DIAMBIL', ''),
        })
    return data


def get_stopwords_indonesian():
    """Mengembalikan set stopwords bahasa Indonesia (NLTK + tambahan manual)"""
    try:
        stop_words = set(stopwords.words('indonesian'))
    except:
        stop_words = set()
    # Tambahan kata umum yang tidak informatif
    extra = {
        'yg', 'nya', 'dgn', 'tdk', 'tidak', 'jadi', 'sih', 'lah', 'kan', 
        'deh', 'ya', 'ni', 'tu', 'ko', 'dong', 'sih', 'juga', 'sangat',
        'kurang', 'banyak', 'sedikit', 'setelah', 'sebelum', 'atau', 'karena',
        'jika', 'maka', 'selalu', 'pernah', 'seluruh', 'semua', 'bagus',
        'baik', 'jelek', 'oke', 'biasa', 'cukup', 'agak', 'terlalu', 'saja',
        'sekali', 'terima', 'kasih', 'makasih', 'tolong', 'mohon'
    }
    stop_words.update(extra)
    return stop_words

def generate_feedback_wordcloud(start_date, end_date):
    """Generate wordcloud dari feedback dalam periode, dengan caching 1 jam."""
    cache_key = f"wordcloud_{start_date}_{end_date}"
    cached_img = cache.get(cache_key)
    if cached_img:
        return cached_img

    from apps.orders.models import Feedback  # hindari circular import

    feedbacks = Feedback.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).exclude(teks__isnull=True).exclude(teks='')

    if not feedbacks:
        return None

    # Gabungkan teks
    raw_text = ' '.join(fb.teks for fb in feedbacks)
    raw_text = raw_text.lower()
    # Hanya huruf (buang angka, tanda baca, emoji)
    raw_text = re.sub(r'[^a-z\s]', '', raw_text)

    # Tokenisasi dengan NLTK (fallback split jika gagal)
    try:
        tokens = word_tokenize(raw_text)
    except:
        tokens = raw_text.split()

    stop_words = get_stopwords_indonesian()
    filtered_tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    if not filtered_tokens:
        return None

    cleaned_text = ' '.join(filtered_tokens)

    # Generate wordcloud
    wordcloud = WordCloud(
        width=800, height=400, background_color='white',
        colormap='Reds', max_words=100
    ).generate(cleaned_text)

    # Konversi ke base64
    img_buffer = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(img_buffer, format='png')
    plt.close()
    img_buffer.seek(0)
    base64_img = base64.b64encode(img_buffer.getvalue()).decode()

    # Simpan cache 1 jam
    cache.set(cache_key, base64_img, 3600)
    return base64_img