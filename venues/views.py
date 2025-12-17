from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg

from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Venue, BlockedDate
from .serializers import VenueSerializer, VenueListSerializer, VenueCreateSerializer, BlockedDateSerializer
from users.models import User

class VenueViewSet(viewsets.ModelViewSet):
    """ViewSet for managing venues"""
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'is_active']
    search_fields = ['name', 'city', 'address', 'description']
    ordering_fields = ['price_per_day', 'capacity', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VenueCreateSerializer
        elif self.action == 'list':
            return VenueListSerializer
        return VenueSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # If vendor, show only their venues
        if user.role == 'VENDOR':
            return Venue.objects.filter(owner=user)
        
        # If renter, show only active venues
        elif user.role == 'RENTER':
            return Venue.objects.filter(is_active=True)
        
        # Admin can see all
        return Venue.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle venue active status (vendor only)"""
        venue = self.get_object()
        
        # Check permission
        if venue.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only venue owner can change status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        venue.is_active = not venue.is_active
        venue.save()
        
        return Response({
            'message': f"Venue {'activated' if venue.is_active else 'deactivated'} successfully",
            'is_active': venue.is_active
        })
    
    @action(detail=True, methods=['get'])
    def blocked_dates(self, request, pk=None):
        """Get blocked dates for a venue"""
        venue = self.get_object()
        blocked_dates = venue.blocked_dates.all()
        serializer = BlockedDateSerializer(blocked_dates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def block_date(self, request, pk=None):
        """Block a date for a venue (vendor only)"""
        venue = self.get_object()
        
        # Check permission
        if venue.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only venue owner can block dates'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        date = request.data.get('date')
        reason = request.data.get('reason', '')
        
        if not date:
            return Response(
                {'error': 'Date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if date is already blocked
        if venue.blocked_dates.filter(date=date).exists():
            return Response(
                {'error': 'Date is already blocked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create blocked date
        blocked_date = BlockedDate.objects.create(
            venue=venue,
            date=date,
            reason=reason
        )
        
        return Response({
            'message': 'Date blocked successfully',
            'blocked_date': BlockedDateSerializer(blocked_date).data
        }, status=status.HTTP_201_CREATED)

class AvailableVenuesView(generics.ListAPIView):
    """Get available venues for given dates"""
    serializer_class = VenueListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        city = self.request.query_params.get('city')
        min_capacity = self.request.query_params.get('min_capacity')
        
        queryset = Venue.objects.filter(is_active=True)
        
        # Filter by city
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        # Filter by capacity
        if min_capacity:
            queryset = queryset.filter(capacity__gte=min_capacity)
        
        # Filter by availability if dates provided
        if start_date and end_date:
            # Exclude venues with blocked dates in the range
            queryset = queryset.exclude(
                blocked_dates__date__gte=start_date,
                blocked_dates__date__lte=end_date
            )
            
            # Exclude venues with conflicting bookings
            from booking.models import Booking
            booked_venue_ids = Booking.objects.filter(
                status__in=['PENDING', 'CONFIRMED'],
                start_date__lte=end_date,
                end_date__gte=start_date
            ).values_list('venue_id', flat=True)
            
            queryset = queryset.exclude(id__in=booked_venue_ids)
        
        return queryset

class MyVenuesView(generics.ListAPIView):
    """Get venues owned by current user (vendor only)"""
    serializer_class = VenueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != 'VENDOR':
            return Venue.objects.none()
        
        return Venue.objects.filter(owner=self.request.user)