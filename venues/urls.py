from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('venues', views.VenueViewSet, basename='venue')

urlpatterns = router.urls