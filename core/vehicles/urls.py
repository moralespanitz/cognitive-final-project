"""
URL patterns for vehicles app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DriverViewSet, VehicleViewSet, TripViewSet

router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'trips', TripViewSet, basename='trip')

urlpatterns = [
    path('', include(router.urls)),
]
