"""
Serializers for tracking app.
"""

from rest_framework import serializers
from .models import GPS_Location


class GPS_LocationSerializer(serializers.ModelSerializer):
    """Serializer for GPS_Location model."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)

    class Meta:
        model = GPS_Location
        fields = [
            'id', 'vehicle', 'vehicle_plate', 'latitude', 'longitude',
            'speed', 'heading', 'accuracy', 'altitude', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class GPS_LocationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating GPS locations (from vehicle devices)."""

    class Meta:
        model = GPS_Location
        fields = [
            'vehicle', 'latitude', 'longitude', 'speed',
            'heading', 'accuracy', 'altitude'
        ]


class LiveLocationSerializer(serializers.ModelSerializer):
    """Lightweight serializer for real-time location updates."""

    class Meta:
        model = GPS_Location
        fields = ['vehicle', 'latitude', 'longitude', 'speed', 'heading', 'timestamp']
