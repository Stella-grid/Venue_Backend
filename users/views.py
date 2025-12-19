from django.shortcuts import render

# Create your views here.

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Favorite
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    UserUpdateSerializer,
    FavoriteSerializer
)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
def profile(request):
    """Get or update user profile"""
    
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def add_favorite(request):
    """Add a venue to favorites"""
    venue_id = request.data.get('venue_id')
    
    if not venue_id:
        return Response({'error': 'venue_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        venue_id=venue_id
    )
    
    if created:
        return Response({'message': 'Added to favorites'}, status=status.HTTP_201_CREATED)
    return Response({'message': 'Already in favorites'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_favorites(request):
    """Get user's favorite venues"""
    favorites = Favorite.objects.filter(user=request.user).select_related('venue')
    
    from venues.serializers import VenueListSerializer
    venues = [f.venue for f in favorites]
    serializer = VenueListSerializer(venues, many=True, context={'request': request})
    
    return Response({'venues': serializer.data})


@api_view(['DELETE'])
def remove_favorite(request, venue_id):
    """Remove a venue from favorites"""
    deleted_count, _ = Favorite.objects.filter(
        user=request.user, 
        venue_id=venue_id
    ).delete()
    
    if deleted_count > 0:
        return Response({'message': 'Removed from favorites'}, status=status.HTTP_200_OK)
    return Response({'error': 'Favorite not found'}, status=status.HTTP_404_NOT_FOUND)