from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'venue', 'renter', 'start_date', 
                    'end_date', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'event_type', 'start_date', 'created_at')
    search_fields = ('booking_reference', 'venue__name', 'renter__email', 
                     'renter__first_name', 'renter__last_name')
    readonly_fields = ('booking_reference', 'subtotal', 'commission', 
                      'deposit_amount', 'total_amount', 'created_at', 'updated_at')
    fieldsets = (
        ('Booking Info', {
            'fields': ('booking_reference', 'venue', 'renter', 'start_date', 'end_date')
        }),
        ('Event Details', {
            'fields': ('guests_count', 'event_type', 'contact_phone', 'special_requests')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'commission', 'deposit_amount', 'total_amount')
        }),
        ('Status & Payment', {
            'fields': ('status', 'rejection_reason', 'deposit_paid', 'full_payment_paid', 
                      'payment_method', 'confirmed_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    date_hierarchy = 'start_date'