from rest_framework import serializers
from .models import Venue, VenueImage, Amenity, VenueAmenity, BlockedDate

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon']


class VenueImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VenueImage
        fields = ['id', 'image', 'image_url', 'is_primary']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class VenueListSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True)
    available = serializers.SerializerMethodField()
    
    class Meta:
        model = Venue
        fields = ['id', 'name', 'city', 'capacity', 'price_per_day', 'rating', 
                  'reviews_count', 'images', 'amenities', 'available']
    
    def get_images(self, obj):
        request = self.context.get('request')
        images = obj.images.all()[:2]
        image_urls = []
        for img in images:
            if request:
                image_urls.append(request.build_absolute_uri(img.image.url))
            else:
                image_urls.append(img.image.url)
        return image_urls
    
    def get_amenities(self, obj):
        return [va.amenity.name for va in obj.venueamenity_set.select_related('amenity').all()]
    
    def get_available(self, obj):
        request_date = self.context.get('date')
        if request_date:
            return not obj.blocked_dates.filter(date=request_date).exists()
        return True


class VenueDetailSerializer(serializers.ModelSerializer):
    images = VenueImageSerializer(many=True, read_only=True)
    amenities = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Venue
        fields = ['id', 'name', 'description', 'city', 'address', 'latitude', 
                  'longitude', 'capacity', 'price_per_day', 'deposit_percentage', 
                  'commission_percentage', 'cancellation_policy', 'rules', 
                  'rating', 'reviews_count', 'images', 'amenities', 'owner', 
                  'is_active', 'created_at']
    
    def get_amenities(self, obj):
        amenities = obj.venueamenity_set.select_related('amenity').all()
        return [va.amenity.name for va in amenities]
    
    def get_owner(self, obj):
        return {
            'id': obj.owner.id,
            'name': f"{obj.owner.first_name} {obj.owner.last_name}",
            'phone': obj.owner.phone
        }


class VenueCreateSerializer(serializers.ModelSerializer):
    amenities = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    blocked_dates = serializers.ListField(
        child=serializers.DateField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Venue
        exclude = ['owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        amenities = validated_data.pop('amenities', [])
        images = validated_data.pop('images', [])
        blocked_dates = validated_data.pop('blocked_dates', [])
        
        venue = Venue.objects.create(**validated_data)
        
        for amenity_name in amenities:
            amenity, _ = Amenity.objects.get_or_create(name=amenity_name.strip())
            VenueAmenity.objects.create(venue=venue, amenity=amenity)
        
        for idx, image in enumerate(images):
            VenueImage.objects.create(
                venue=venue,
                image=image,
                is_primary=(idx == 0)
            )
        
        for date in blocked_dates:
            BlockedDate.objects.create(venue=venue, date=date)
        
        return venue
    
    def update(self, instance, validated_data):
        amenities = validated_data.pop('amenities', None)
        images = validated_data.pop('images', None)
        blocked_dates = validated_data.pop('blocked_dates', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if amenities is not None:
            instance.venueamenity_set.all().delete()
            for amenity_name in amenities:
                amenity, _ = Amenity.objects.get_or_create(name=amenity_name.strip())
                VenueAmenity.objects.create(venue=instance, amenity=amenity)
        
        if images is not None:
            for image in images:
                VenueImage.objects.create(venue=instance, image=image)
        
        if blocked_dates is not None:
            instance.blocked_dates.all().delete()
            for date in blocked_dates:
                BlockedDate.objects.create(venue=instance, date=date)
        
        return instance