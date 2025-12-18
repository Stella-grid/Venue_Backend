
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Booking
from .serializers import BookingSerializer, BookingListSerializer, BookingDetailSerializer
from venues.models import Venue

class UserBookingsView(generics.ListAPIView):
    """Get all bookings for current user"""
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'RENTER':
            return Booking.objects.filter(renter=user).select_related('venue', 'renter')
        elif user.role == 'VENDOR':
            return Booking.objects.filter(venue__owner=user).select_related('venue', 'renter')
        
        return Booking.objects.none()

class UpcomingBookingsView(generics.ListAPIView):
    """Get upcoming bookings for current user"""
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        
        if user.role == 'RENTER':
            return Booking.objects.filter(
                renter=user,
                start_date__gte=today,
                status__in=['PENDING', 'CONFIRMED']
            ).select_related('venue', 'renter')
        elif user.role == 'VENDOR':
            return Booking.objects.filter(
                venue__owner=user,
                start_date__gte=today,
                status__in=['PENDING', 'CONFIRMED']
            ).select_related('venue', 'renter')
        
        return Booking.objects.none()

class PastBookingsView(generics.ListAPIView):
    """Get past bookings for current user"""
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        
        if user.role == 'RENTER':
            return Booking.objects.filter(
                renter=user
            ).filter(
                Q(end_date__lt=today) | Q(status='COMPLETED')
            ).select_related('venue', 'renter')
        elif user.role == 'VENDOR':
            return Booking.objects.filter(
                venue__owner=user
            ).filter(
                Q(end_date__lt=today) | Q(status='COMPLETED')
            ).select_related('venue', 'renter')
        
        return Booking.objects.none()

class BookingDetailView(generics.RetrieveAPIView):
    """Get detailed booking information"""
    queryset = Booking.objects.all()
    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        booking = super().get_object()
        
        
        user = self.request.user
        if booking.renter != user and booking.venue.owner != user and not user.is_staff:
            self.permission_denied(self.request, 'You do not have permission to view this booking')
        
        return booking

class CancelBookingView(generics.UpdateAPIView):
    """Cancel a booking"""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        
      
        if booking.renter != request.user:
            return Response(
                {'error': 'Only the renter can cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
       
        if booking.status in ['COMPLETED', 'CANCELLED', 'REJECTED']:
            return Response(
                {'error': 'Cannot cancel this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        time_to_start = booking.start_date - timezone.now().date()
        if time_to_start.days < 1 and booking.status == 'CONFIRMED':
            return Response(
                {'error': 'Cannot cancel within 24 hours of start date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
       
        booking.status = 'CANCELLED'
        booking.rejection_reason = request.data.get('reason', 'Cancelled by renter')
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response({
            'message': 'Booking cancelled successfully',
            'booking': serializer.data
        })

class CalculatePriceView(generics.GenericAPIView):
    """Calculate price for a booking"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        venue_id = request.data.get('venue_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not all([venue_id, start_date, end_date]):
            return Response(
                {'error': 'venue_id, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            venue = Venue.objects.get(id=venue_id, is_active=True)
        except Venue.DoesNotExist:
            return Response(
                {'error': 'Venue not found or not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        days = (end - start).days + 1
        
        subtotal = venue.price_per_day * days
        commission = subtotal * (venue.commission_percentage / 100)
        deposit = subtotal * (venue.deposit_percentage / 100)
        total = subtotal + commission
        
        return Response({
            'venue': {
                'id': venue.id,
                'name': venue.name,
                'city': venue.city
            },
            'dates': {
                'start_date': start_date,
                'end_date': end_date,
                'days': days
            },
            'pricing': {
                'price_per_day': float(venue.price_per_day),
                'subtotal': float(subtotal),
                'commission': float(commission),
                'deposit_percentage': float(venue.deposit_percentage),
                'deposit_amount': float(deposit),
                'total': float(total)
            }
        })