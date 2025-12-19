from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Profile
    path('users/me/', views.profile, name='profile'),
    
    # Favorites
    path('users/favorites/', views.add_favorite, name='add_favorite'),
    path('users/favorites/list/', views.get_favorites, name='get_favorites'),
    path('users/favorites/<int:venue_id>/', views.remove_favorite, name='remove_favorite'),
]