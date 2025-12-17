from rest_framework import serializers
from .models import Booking
from venues.serializers import VenueListSerializer
from users.serializers import UserSerializer

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_reference', 'subtotal', 'commission', 
                          'deposit_amount', 'total_amount', 'created_at', 'updated_at']

class BookingListSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.name', read_only=True)
    venue_city = serializers.CharField(source='venue.city', read_only=True)
    renter_name = serializers.SerializerMethodField()
    days = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_reference', 'venue_name', 'venue_city', 
                  'renter_name', 'start_date', 'end_date', 'days', 
                  'event_type', 'status', 'total_amount', 'created_at']
    
    def get_renter_name(self, obj):
        return obj.renter.full_name
    
    def get_days(self, obj):
        return obj.duration_days

class BookingDetailSerializer(serializers.ModelSerializer):
    venue = VenueListSerializer(read_only=True)
    renter = UserSerializer(read_only=True)
    days = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
    
    def get_days(self, obj):
        return obj.duration_days