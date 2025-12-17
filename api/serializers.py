from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from venues.models import Venue, BlockedDate
from booking.models import Booking

class BookingCreateSerializer(serializers.Serializer):
    """Complex serializer for creating bookings with validation."""
    venue_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    guests_count = serializers.IntegerField(min_value=1)
    event_type = serializers.ChoiceField(choices=Booking.EVENT_TYPE_CHOICES)
    contact_phone = serializers.CharField(max_length=20)
    special_requests = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_venue_id(self, value):
        try:
            venue = Venue.objects.get(id=value, is_active=True)
            return venue
        except Venue.DoesNotExist:
            raise serializers.ValidationError("Venue not found or not available")
    
    def validate(self, data):
        venue = data['venue_id']  # This is now a Venue instance after validation
        start_date = data['start_date']
        end_date = data['end_date']
        
        if start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        if start_date < timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the past")
        
        if data['guests_count'] > venue.capacity:
            raise serializers.ValidationError(
                f"Guest count exceeds venue capacity ({venue.capacity})"
            )
        
        # Check blocked dates
        blocked = venue.blocked_dates.filter(
            date__gte=start_date,
            date__lte=end_date
        ).exists()
        
        if blocked:
            raise serializers.ValidationError("Venue is not available for selected dates (blocked)")
        
        # Check conflicting bookings
        conflicting = Booking.objects.filter(
            venue=venue,
            status__in=['PENDING', 'CONFIRMED'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        if conflicting:
            raise serializers.ValidationError("Venue is not available for selected dates (already booked)")
        
        return data
    
    def create(self, validated_data):
        venue = validated_data.pop('venue_id')
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        
        days = (end_date - start_date).days + 1
        
        # Calculate pricing
        subtotal = Decimal(str(venue.price_per_day)) * days
        commission = subtotal * (Decimal(str(venue.commission_percentage)) / Decimal('100'))
        deposit = subtotal * (Decimal(str(venue.deposit_percentage)) / Decimal('100'))
        total = subtotal + commission
        
        # Create booking
        booking = Booking.objects.create(
            venue=venue,
            renter=self.context['request'].user,
            subtotal=subtotal,
            commission=commission,
            deposit_amount=deposit,
            total_amount=total,
            **validated_data
        )
        
        # Optional: You can add notifications later
        # For now, we'll skip notifications to avoid import errors
        
        return booking

class DashboardSerializer(serializers.Serializer):
    """Serializer for vendor dashboard statistics."""
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    this_month_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_bookings = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    total_venues = serializers.IntegerField()
    recent_bookings = serializers.ListField(child=serializers.DictField())