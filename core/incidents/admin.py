from django.contrib import admin
from .models import Incident, Alert


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    """Admin interface for Incident model."""

    list_display = ['vehicle', 'driver', 'type', 'severity', 'detected_at', 'resolved_at']
    list_filter = ['type', 'severity', 'detected_at']
    search_fields = ['vehicle__license_plate', 'driver__license_number', 'description']
    readonly_fields = ['detected_at']
    ordering = ['-detected_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin interface for Alert model."""

    list_display = ['vehicle', 'type', 'priority', 'acknowledged', 'acknowledged_by', 'created_at']
    list_filter = ['priority', 'acknowledged', 'created_at']
    search_fields = ['vehicle__license_plate', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
