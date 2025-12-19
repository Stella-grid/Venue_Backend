from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Venue, VenueImage, Amenity, VenueAmenity, BlockedDate

class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1

class VenueAmenityInline(admin.TabularInline):
    model = VenueAmenity
    extra = 1

class BlockedDateInline(admin.TabularInline):
    model = BlockedDate
    extra = 1

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'owner', 'capacity', 'price_per_day', 'is_active', 'created_at']
    list_filter = ['city', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'address', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VenueImageInline, VenueAmenityInline, BlockedDateInline]
    
    actions = ['deactivate_venues', 'activate_venues']
    
    def deactivate_venues(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} venues were deactivated.')
    deactivate_venues.short_description = "Deactivate selected venues"
    
    def activate_venues(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} venues were activated.')
    activate_venues.short_description = "Activate selected venues"

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name']