
from django.urls import path, include

"""
Central API URL routing
This file can be used if you want all API endpoints under /api/
Currently, we're using individual app URLs in config/urls.py
"""

from django.urls import path, include

urlpatterns = [
    path('', include('users.urls')),
    path('', include('venues.urls')),
    path('', include('booking.urls')),
]