"""
Serializers for vehicles app.
"""

from rest_framework import serializers
from .models import Driver, Vehicle, Trip
from accounts.serializers import UserSerializer


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver model."""

    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Driver
        fields = [
            'id', 'user', 'user_id', 'license_number', 'license_expiry',
            'status', 'rating', 'total_trips', 'photo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'rating', 'total_trips']


class DriverListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for driver lists."""

    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ['id', 'driver_name', 'license_number', 'status', 'rating']

    def get_driver_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for Vehicle model."""

    current_driver = DriverListSerializer(read_only=True)
    current_driver_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'make', 'model', 'year', 'color', 'vin',
            'capacity', 'status', 'current_driver', 'current_driver_id',
            'registration_date', 'insurance_expiry', 'last_service_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for vehicle lists."""

    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'license_plate', 'make', 'model', 'year',
            'status', 'driver_name'
        ]

    def get_driver_name(self, obj):
        if obj.current_driver:
            return obj.current_driver.user.get_full_name() or obj.current_driver.user.username
        return None


class TripSerializer(serializers.ModelSerializer):
    """Serializer for Trip model."""

    vehicle = VehicleListSerializer(read_only=True)
    driver = DriverListSerializer(read_only=True)
    vehicle_id = serializers.IntegerField(write_only=True)
    driver_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'vehicle', 'driver', 'vehicle_id', 'driver_id',
            'start_time', 'end_time', 'start_location', 'end_location',
            'distance', 'duration', 'status', 'fare',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TripListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for trip lists."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)
    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'vehicle_plate', 'driver_name', 'start_time',
            'end_time', 'status', 'distance', 'fare'
        ]

    def get_driver_name(self, obj):
        return obj.driver.user.get_full_name() or obj.driver.user.username
