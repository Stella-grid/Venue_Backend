from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VenueViewSet, AvailableVenuesView, MyVenuesView

router = DefaultRouter()
router.register('', VenueViewSet, basename='venue')

urlpatterns = [
    path('', include(router.urls)),
    path('available/', AvailableVenuesView.as_view(), name='available-venues'),
    path('my-venues/', MyVenuesView.as_view(), name='my-venues'),
]