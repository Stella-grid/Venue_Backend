from django.urls import path
from .views import (
    UserBookingsView,
    UpcomingBookingsView,
    PastBookingsView,
    BookingDetailView,
    CancelBookingView,
    CalculatePriceView
)

urlpatterns = [
    path('', UserBookingsView.as_view(), name='user-bookings'),
    path('upcoming/', UpcomingBookingsView.as_view(), name='upcoming-bookings'),
    path('past/', PastBookingsView.as_view(), name='past-bookings'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('<int:pk>/cancel/', CancelBookingView.as_view(), name='cancel-booking'),
    path('calculate-price/', CalculatePriceView.as_view(), name='calculate-price'),
]