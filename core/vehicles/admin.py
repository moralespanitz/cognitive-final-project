from django.contrib import admin
from .models import Driver, Vehicle, Trip


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    """Admin interface for Driver model."""

    list_display = ['user', 'license_number', 'status', 'rating', 'total_trips', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'user__email', 'license_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin interface for Vehicle model."""

    list_display = ['license_plate', 'make', 'model', 'year', 'status', 'current_driver', 'created_at']
    list_filter = ['status', 'make', 'year', 'created_at']
    search_fields = ['license_plate', 'vin', 'make', 'model']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Admin interface for Trip model."""

    list_display = ['id', 'vehicle', 'driver', 'start_time', 'end_time', 'status', 'distance', 'fare']
    list_filter = ['status', 'start_time']
    search_fields = ['vehicle__license_plate', 'driver__license_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-start_time']
