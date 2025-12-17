from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Venue, BlockedDate

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city', 'capacity', 'price_per_day', 'is_active')
    list_filter = ('city', 'is_active', 'created_at')
    search_fields = ('name', 'owner__email', 'city', 'address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('owner', 'name', 'description', 'city', 'address')
        }),
        ('Pricing', {
            'fields': ('capacity', 'price_per_day', 'commission_percentage', 'deposit_percentage')
        }),
        ('Contact & Details', {
            'fields': ('contact_email', 'contact_phone', 'amenities', 'rules')
        }),
        ('Media', {
            'fields': ('main_image', 'gallery')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ('venue', 'date', 'reason')
    list_filter = ('date', 'venue__city')
    search_fields = ('venue__name', 'reason')
    date_hierarchy = 'date'