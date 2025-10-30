from django.contrib import admin
from .models import GPS_Location


@admin.register(GPS_Location)
class GPS_LocationAdmin(admin.ModelAdmin):
    """Admin interface for GPS_Location model."""

    list_display = ['vehicle', 'latitude', 'longitude', 'speed', 'timestamp']
    list_filter = ['vehicle', 'timestamp']
    search_fields = ['vehicle__license_plate']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
