from django.db import models
from django.core.validators import MinValueValidator
from users.models import User
from venues.models import Venue
import random
import string
from django.utils import timezone

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    ]
    
    EVENT_TYPE_CHOICES = [
        ('WEDDING', 'Wedding'),
        ('CONFERENCE', 'Conference'),
        ('BIRTHDAY', 'Birthday Party'),
        ('CORPORATE', 'Corporate Event'),
        ('GRADUATION', 'Graduation'),
        ('OTHER', 'Other'),
    ]
    
    booking_reference = models.CharField(max_length=20, unique=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    guests_count = models.IntegerField(validators=[MinValueValidator(1)])
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    contact_phone = models.CharField(max_length=20)
    special_requests = models.TextField(blank=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['venue', 'start_date', 'end_date']),
            models.Index(fields=['renter', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.booking_reference} - {self.venue.name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_reference()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_reference():
        return 'BOOK-' + ''.join(random.choices(string.digits, k=8))