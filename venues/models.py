from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from django.utils import timezone

class Venue(models.Model):
    CITY_CHOICES = [
        ('Douala', 'Douala'),
        ('Yaounde', 'Yaoundé'),
        ('Bafoussam', 'Bafoussam'),
        ('Garoua', 'Garoua'),
        ('Bamenda', 'Bamenda'),
        ('Limbe', 'Limbe'),
        ('Kribi', 'Kribi'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venues')
    name = models.CharField(max_length=200)
    description = models.TextField()
    city = models.CharField(max_length=50, choices=CITY_CHOICES)
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    deposit_percentage = models.IntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    commission_percentage = models.IntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    cancellation_policy = models.TextField(default="Full refund 7 days before event date")
    rules = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)
    
    class Meta:
        db_table = 'venues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['price_per_day']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    @property
    def rating(self):
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating else 0.0
    
    @property
    def reviews_count(self):
        return self.reviews.count()


class VenueImage(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venues/%Y/%m/')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'venue_images'
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.venue.name}"


class Amenity(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'amenities'
        verbose_name_plural = 'Amenities'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class VenueAmenity(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'venue_amenities'
        unique_together = ('venue', 'amenity')
    
    def __str__(self):
        return f"{self.venue.name} - {self.amenity.name}"


class BlockedDate(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='blocked_dates')
    date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blocked_dates'
        unique_together = ('venue', 'date')
        ordering = ['date']
        indexes = [
            models.Index(fields=['venue', 'date']),
        ]
    
    def __str__(self):
        return f"{self.venue.name} - {self.date}"