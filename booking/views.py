
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Q
from .models import Booking
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
)

class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'event_type']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'RENTER':
            return Booking.objects.filter(renter=user).select_related('venue', 'renter')
        elif user.role == 'VENDOR':
            return Booking.objects.filter(venue__owner=user).select_related('venue', 'renter')
        
        return Booking.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action == 'list':
            return BookingListSerializer
        return BookingDetailSerializer
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
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
            'upcoming': BookingListSerializer(upcoming, many=True).data,
            'past': BookingListSerializer(past, many=True).data,
            'pending': BookingListSerializer(pending, many=True).data,
            'cancelled': BookingListSerializer(cancelled, many=True).data
        })
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        
        if booking.venue.owner != request.user:
            return Response(
                {'error': 'Only venue owner can update booking status'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        rejection_reason = request.data.get('rejection_reason', '')
        
        if new_status == 'CONFIRMED':
            booking.status = 'CONFIRMED'
            booking.confirmed_at = timezone.now()
            
           
        
        elif new_status == 'REJECTED':
            booking.status = 'REJECTED'
            booking.rejection_reason = rejection_reason
            
            
               
        
        elif new_status == 'COMPLETED':
            booking.status = 'COMPLETED'
            booking.completed_at = timezone.now()
        
        else:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.save()
        
        return Response(BookingDetailSerializer(booking, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        if booking.renter != request.user:
            return Response(
                {'error': 'Only the renter can cancel this booking'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {'error': 'Cannot cancel this booking'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'CANCELLED'
        booking.rejection_reason = request.data.get('reason', 'Cancelled by renter')
        booking.save()
        
        

@api_view(['GET'])
def vendor_dashboard(request):
    if request.user.role != 'VENDOR':
        return Response(
            {'error': 'Only vendors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    from venues.models import Venue
    
    venues = Venue.objects.filter(owner=request.user)
    bookings = Booking.objects.filter(venue__owner=request.user)
    
    this_month_start = timezone.now().replace(day=1).date()
    this_month_bookings = bookings.filter(
        created_at__gte=this_month_start,
        status='COMPLETED'
    )
    
    total_earnings = bookings.filter(status='COMPLETED').aggregate(
        total=Sum('subtotal')
    )['total'] or 0
    
    this_month_earnings = this_month_bookings.aggregate(
        total=Sum('subtotal')
    )['total'] or 0
    
    pending_bookings = bookings.filter(status='PENDING').count()
    total_bookings = bookings.count()
    
    recent_bookings = bookings.order_by('-created_at')[:5]
    
    return Response({
        'total_earnings': float(total_earnings),
        'this_month_earnings': float(this_month_earnings),
        'pending_bookings': pending_bookings,
        'total_bookings': total_bookings,
        'total_venues': venues.count(),
        'recent_bookings': BookingListSerializer(recent_bookings, many=True).data
    })


@api_view(['GET'])
def vendor_bookings(request):
    if request.user.role != 'VENDOR':
        return Response(
            {'error': 'Only vendors can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    bookings = Booking.objects.filter(venue__owner=request.user).select_related('venue', 'renter')
    
    return Response({
        'pending': BookingListSerializer(
            bookings.filter(status='PENDING'), many=True) })