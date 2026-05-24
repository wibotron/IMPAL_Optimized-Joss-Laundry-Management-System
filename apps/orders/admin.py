from django.contrib import admin
from .models import Order, Feedback
# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = ('kode_nota', 'nama_customer', 'nomor_hp', 'paket', 'berat', 'total_harga', 'progress_status', 'payment_status', 'tanggal_order')
    list_filter = ('progress_status', 'payment_status', 'paket')
    search_fields = ('kode_nota', 'nama_customer', 'nomor_hp')
    readonly_fields = ('kode_nota', 'total_harga', 'tanggal_order', 'tanggal_update')

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('order', 'rating', 'created_at', 'has_reply')
    list_filter = ('rating', 'created_at')
    def has_reply(self, obj):
        return bool(obj.reply)
    has_reply.boolean = True

admin.site.register(Order, OrderAdmin)
admin.site.register(Feedback, FeedbackAdmin)