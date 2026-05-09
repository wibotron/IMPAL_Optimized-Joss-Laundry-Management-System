from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import LaundryPackage

@admin.register(LaundryPackage)
class LaundryPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_kg', 'estimated_days', 'is_active', 'is_valid_status')
    list_filter = ('is_active', 'estimated_days')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def is_valid_status(self, obj):
        return obj.is_valid
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid Saat Ini'