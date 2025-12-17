from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, vendor_dashboard, vendor_bookings

router = DefaultRouter()
router.register('bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
    path('vendor/dashboard/', vendor_dashboard, name='vendor_dashboard'),
    path('vendor/bookings/', vendor_bookings, name='vendor_bookings'),
    path('my-bookings/', BookingViewSet.as_view({'get': 'my_bookings'}), name='my_bookings'),
]