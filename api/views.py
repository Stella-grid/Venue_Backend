from django.shortcuts import render

# Create your views here.
# OLD imports (in your 

from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta

from booking.models import Booking
from venues.models import Venue
from users.models import User

from api.serializers import BookingCreateSerializer, DashboardSerializer
from booking.serializers import BookingDetailSerializer, BookingListSerializer

class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'event_type']
    ordering_fields = ['created_at', 'start_date', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'RENTER':
            return Booking.objects.filter(renter=user).select_related('venue', 'renter')
        elif user.role == 'VENDOR':
            return Booking.objects.filter(venue__owner=user).select_related('venue', 'renter')
        else:
            # Admin can see all
            return Booking.objects.all().select_related('venue', 'renter')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        else:
            return BookingDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get bookings organized by status for renters."""
        if request.user.role != 'RENTER':
            return Response(
                {'error': 'Only renters can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bookings = self.get_queryset()
        today = timezone.now().date()
        
        upcoming = bookings.filter(
            start_date__gte=today,
            status__in=['PENDING', 'CONFIRMED']
        )
        past = bookings.filter(
            Q(end_date__lt=today) | Q(status='COMPLETED')
        )
        pending = bookings.filter(status='PENDING')
        cancelled = bookings.filter(status='CANCELLED')
        
        return Response({
            'upcoming': BookingListSerializer(upcoming, many=True, context={'request': request}).data,
            'past': BookingListSerializer(past, many=True, context={'request': request}).data,
            'pending': BookingListSerializer(pending, many=True, context={'request': request}).data,
            'cancelled': BookingListSerializer(cancelled, many=True, context={'request': request}).data
        })
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update booking status (for vendors)."""
        booking = self.get_object()
        
        # Check permission
        if booking.venue.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only venue owner can update booking status'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Check if status transition is valid
        valid_transitions = {
            'PENDING': ['CONFIRMED', 'REJECTED'],
            'CONFIRMED': ['COMPLETED', 'CANCELLED'],
        }
        
        if new_status not in valid_transitions.get(booking.status, []):
            return Response(
                {'error': f'Cannot change status from {booking.status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update booking
        if new_status == 'CONFIRMED':
            booking.status = 'CONFIRMED'
            booking.confirmed_at = timezone.now()
            booking.rejection_reason = ''
            
        elif new_status == 'REJECTED':
            booking.status = 'REJECTED'
            booking.rejection_reason = rejection_reason or 'Booking rejected by venue owner'
            
        elif new_status == 'COMPLETED':
            booking.status = 'COMPLETED'
            booking.completed_at = timezone.now()
            
        elif new_status == 'CANCELLED':
            booking.status = 'CANCELLED'
            booking.rejection_reason = request.data.get('reason', 'Cancelled by venue owner')
            
        else:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.save()
        
        return Response(BookingDetailSerializer(booking, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking (for renters)."""
        booking = self.get_object()
        
        if booking.renter != request.user:
            return Response(
                {'error': 'Only the renter can cancel this booking'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking can be cancelled
        if booking.status in ['COMPLETED', 'CANCELLED', 'REJECTED']:
            return Response(
                {'error': 'Cannot cancel this booking'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check cancellation policy (e.g., within 24 hours of start date)
        time_to_start = booking.start_date - timezone.now().date()
        if time_to_start.days < 1 and booking.status == 'CONFIRMED':
            return Response(
                {'error': 'Cannot cancel within 24 hours of start date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'CANCELLED'
        booking.rejection_reason = request.data.get('reason', 'Cancelled by renter')
        booking.save()
        
        return Response({
            'message': 'Booking cancelled successfully',
            'booking': BookingDetailSerializer(booking, context={'request': request}).data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_dashboard(request):
    """Get vendor dashboard statistics."""
    if request.user.role != 'VENDOR':
        return Response(
            {'error': 'Only vendors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    venues = Venue.objects.filter(owner=request.user)
    bookings = Booking.objects.filter(venue__owner=request.user)
    
    # This month's start date
    this_month_start = timezone.now().replace(day=1).date()
    
    # This month's completed bookings
    this_month_bookings = bookings.filter(
        created_at__date__gte=this_month_start,
        status='COMPLETED'
    )
    
    # Total earnings (only from completed bookings)
    total_earnings = bookings.filter(status='COMPLETED').aggregate(
        total=Sum('subtotal')
    )['total'] or 0
    
    # This month's earnings
    this_month_earnings = this_month_bookings.aggregate(
        total=Sum('subtotal')
    )['total'] or 0
    
    # Counts
    pending_bookings = bookings.filter(status='PENDING').count()
    total_bookings = bookings.count()
    
    # Recent bookings (last 5)
    recent_bookings = bookings.order_by('-created_at')[:5]
    recent_bookings_data = BookingListSerializer(recent_bookings, many=True, context={'request': request}).data
    
    return Response({
        'total_earnings': float(total_earnings),
        'this_month_earnings': float(this_month_earnings),
        'pending_bookings': pending_bookings,
        'total_bookings': total_bookings,
        'total_venues': venues.count(),
        'recent_bookings': recent_bookings_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_bookings(request):
    """Get vendor bookings grouped by status."""
    if request.user.role != 'VENDOR':
        return Response(
            {'error': 'Only vendors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    bookings = Booking.objects.filter(venue__owner=request.user).select_related('venue', 'renter')
    
    return Response({
        'pending': BookingListSerializer(
            bookings.filter(status='PENDING'), many=True, context={'request': request}
        ).data,
        'confirmed': BookingListSerializer(
            bookings.filter(status='CONFIRMED'), many=True, context={'request': request}
        ).data,
        'completed': BookingListSerializer(
            bookings.filter(status='COMPLETED'), many=True, context={'request': request}
        ).data,
        'cancelled': BookingListSerializer(
            bookings.filter(status='CANCELLED'), many=True, context={'request': request}
        ).data,
        'rejected': BookingListSerializer(
            bookings.filter(status='REJECTED'), many=True, context={'request': request}
        ).data
    })