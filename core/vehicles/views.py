"""
Views for vehicles app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Driver, Vehicle, Trip
from .serializers import (
    DriverSerializer,
    DriverListSerializer,
    VehicleSerializer,
    VehicleListSerializer,
    TripSerializer,
    TripListSerializer
)


class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet for Driver model."""

    queryset = Driver.objects.all().select_related('user')
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return DriverListSerializer
        return DriverSerializer

    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        """Get all trips for a driver."""
        driver = self.get_object()
        trips = driver.trips.all()
        serializer = TripListSerializer(trips, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get driver performance metrics."""
        driver = self.get_object()
        return Response({
            'total_trips': driver.total_trips,
            'rating': driver.rating,
            'status': driver.status,
            # Add more metrics as needed
        })


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for Vehicle model."""

    queryset = Vehicle.objects.all().select_related('current_driver__user')
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer

    @action(detail=True, methods=['get'])
    def location(self, request, pk=None):
        """Get latest vehicle location."""
        vehicle = self.get_object()
        latest_location = vehicle.locations.first()
        if latest_location:
            from tracking.serializers import GPS_LocationSerializer
            serializer = GPS_LocationSerializer(latest_location)
            return Response(serializer.data)
        return Response({'detail': 'No location data available.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        """Assign a driver to this vehicle."""
        vehicle = self.get_object()
        driver_id = request.data.get('driver_id')
        if not driver_id:
            return Response(
                {'error': 'driver_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            driver = Driver.objects.get(id=driver_id)
            vehicle.current_driver = driver
            vehicle.save()
            serializer = self.get_serializer(vehicle)
            return Response(serializer.data)
        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TripViewSet(viewsets.ModelViewSet):
    """ViewSet for Trip model."""

    queryset = Trip.objects.all().select_related('vehicle', 'driver__user')
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return TripListSerializer
        return TripSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by vehicle if provided
        vehicle_id = self.request.query_params.get('vehicle_id')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        # Filter by driver if provided
        driver_id = self.request.query_params.get('driver_id')
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
