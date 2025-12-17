from django.db import models
from users.models import User

class Venue(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venues')
    name = models.CharField(max_length=255)
    description = models.TextField()
    city = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.IntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    deposit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.0)
    is_active = models.BooleanField(default=True)
    
    # Additional venue details
    amenities = models.TextField(blank=True, null=True)
    rules = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Images
    main_image = models.ImageField(upload_to='venues/', blank=True, null=True)
    gallery = models.TextField(blank=True, null=True)  # JSON field for multiple images
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'venues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['owner', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    def get_daily_price(self):
        """Get the daily price of the venue."""
        return self.price_per_day
    
    def calculate_total_price(self, days):
        """Calculate total price for given number of days."""
        return self.price_per_day * days

class BlockedDate(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='blocked_dates')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'venue_blocked_dates'
        unique_together = ['venue', 'date']
    
    def __str__(self):
        return f"{self.venue.name} - {self.date}"