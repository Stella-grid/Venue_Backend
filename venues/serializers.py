from rest_framework import serializers
from .models import Venue, BlockedDate
from users.serializers import UserSerializer

class BlockedDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedDate
        fields = ['id', 'date', 'reason']

class VenueSerializer(serializers.ModelSerializer):
    owner_info = UserSerializer(source='owner', read_only=True)
    blocked_dates = BlockedDateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Venue
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

class VenueListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ['id', 'name', 'city', 'capacity', 'price_per_day', 
                  'main_image', 'is_active', 'created_at']

class VenueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ['name', 'description', 'city', 'address', 'capacity', 
                  'price_per_day', 'commission_percentage', 'deposit_percentage',
                  'amenities', 'rules', 'contact_email', 'contact_phone', 'main_image']
        
    def create(self, validated_data):
        # Set owner to current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)