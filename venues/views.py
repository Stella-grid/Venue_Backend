from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from datetime import datetime
from .models import Venue
from .serializers import (
    VenueListSerializer,
    VenueDetailSerializer,
    VenueCreateSerializer,
)

class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['price_per_day', 'created_at', 'capacity']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VenueListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VenueCreateSerializer
        return VenueDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'featured', 'check_availability']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        queryset = queryset.annotate(rating=Avg('reviews__rating'))
        
        if self.request.user.is_authenticated and self.request.user.role == 'VENDOR':
            if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
                queryset = Venue.objects.filter(owner=self.request.user).annotate(
                    rating=Avg('reviews__rating')
                )
        
        capacity_min = self.request.query_params.get('capacity_min')
        capacity_max = self.request.query_params.get('capacity_max')
        if capacity_min:
            queryset = queryset.filter(capacity__gte=capacity_min)
        if capacity_max:
            queryset = queryset.filter(capacity__lte=capacity_max)
        
        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        if price_min:
            queryset = queryset.filter(price_per_day__gte=price_min)
        if price_max:
            queryset = queryset.filter(price_per_day__lte=price_max)
        
        amenities = self.request.query_params.get('amenities')
        if amenities:
            amenity_list = [a.strip() for a in amenities.split(',')]
            for amenity in amenity_list:
                queryset = queryset.filter(venueamenity__amenity__name__iexact=amenity)
        
        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                from booking.models import Booking
                queryset = queryset.exclude(
                    Q(blocked_dates__date=check_date) |
                    Q(booking__start_date__lte=check_date, 
                      booking__end_date__gte=check_date, 
                      booking__status__in=['PENDING', 'CONFIRMED'])
                )
            except ValueError:
                pass
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        venues = self.get_queryset().annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating', '-created_at')[:6]
        
        serializer = VenueListSerializer(venues, many=True, context={'request': request})
        return Response({'venues': serializer.data})
    
    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        venue = self.get_object()
        
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if start_date >= end_date:
            return Response(
                {'error': 'End date must be after start date'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        days = (end_date - start_date).days + 1
        
        blocked = venue.blocked_dates.filter(
            date__gte=start_date,
            date__lte=end_date
        ).exists()
        
        from booking.models import Booking
        conflicting_bookings = Booking.objects.filter(
            venue=venue,
            status__in=['PENDING', 'CONFIRMED'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        available = not (blocked or conflicting_bookings)
        
        subtotal = float(venue.price_per_day) * days
        commission = subtotal * (venue.commission_percentage / 100)
        deposit = subtotal * (venue.deposit_percentage / 100)
        total = subtotal + commission
        
        return Response({
            'available': available,
            'blocked_dates': list(venue.blocked_dates.filter(
                date__gte=start_date,
                date__lte=end_date
            ).values_list('date', flat=True)),
            'price_breakdown': {
                'days': days,
                'price_per_day': float(venue.price_per_day),
                'subtotal': round(subtotal, 2),
                'commission': round(commission, 2),
                'deposit': round(deposit, 2),
                'total': round(total, 2)
            }
        })