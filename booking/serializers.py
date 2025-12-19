from rest_framework import serializers
from django.utils import timezone
from .models import Booking
from venues.models import Venue

class BookingCreateSerializer(serializers.Serializer):
    venue_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    guests_count = serializers.IntegerField(min_value=1)
    event_type = serializers.ChoiceField(choices=Booking.EVENT_TYPE_CHOICES)
    contact_phone = serializers.CharField(max_length=20)
    special_requests = serializers.CharField(required=False, allow_blank=True)
    
    def validate_venue_id(self, value):
        try:
            venue = Venue.objects.get(id=value, is_active=True)
            return venue
        except Venue.DoesNotExist:
            raise serializers.ValidationError("Venue not found or not available")
    
    def validate(self, data):
        venue = data['venue_id']
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
        
        blocked = venue.blocked_dates.filter(
            date__gte=start_date,
            date__lte=end_date
        ).exists()
        
        if blocked:
            raise serializers.ValidationError("Venue is not available for selected dates (blocked)")
        
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
        
        days = (validated_data['end_date'] - validated_data['start_date']).days + 1
        subtotal = float(venue.price_per_day) * days
        commission = subtotal * (venue.commission_percentage / 100)
        deposit = subtotal * (venue.deposit_percentage / 100)
        total = subtotal + commission
        
        booking = Booking.objects.create(
            venue=venue,
            renter=self.context['request'].user,
            subtotal=subtotal,
            commission=commission,
            deposit_amount=deposit,
            total_amount=total,
            **validated_data
        )
        
        from notifications.models import Notification
        Notification.objects.create(
            user=venue.owner,
            type='NEW_BOOKING',
            message=f"New booking request for {venue.name} from {booking.renter.first_name}",
            link=f"/vendor/bookings/{booking.id}"
        )
        
        return booking


class BookingDetailSerializer(serializers.ModelSerializer):
    venue = serializers.SerializerMethodField()
    renter = serializers.SerializerMethodField()
    days = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
    
    def get_venue(self, obj):
        from venues.serializers import VenueListSerializer
        return VenueListSerializer(obj.venue, context=self.context).data
    
    def get_renter(self, obj):
        return {
            'id': obj.renter.id,
            'name': f"{obj.renter.first_name} {obj.renter.last_name}",
            'email': obj.renter.email,
            'phone': obj.renter.phone
        }
    
    def get_days(self, obj):
        return (obj.end_date - obj.start_date).days + 1


class BookingListSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.name', read_only=True)
    venue_city = serializers.CharField(source='venue.city', read_only=True)
    days = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_reference', 'venue_name', 'venue_city', 'start_date', 
                  'end_date', 'days', 'event_type', 'status', 'total_amount', 'created_at']
    
    def get_days(self, obj):
        return (obj.end_date - obj.start_date).days + 1