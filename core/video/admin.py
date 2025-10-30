from django.contrib import admin
from .models import VideoStream, VideoArchive


@admin.register(VideoStream)
class VideoStreamAdmin(admin.ModelAdmin):
    """Admin interface for VideoStream model."""

    list_display = ['vehicle', 'camera_position', 'status', 'started_at', 'ended_at']
    list_filter = ['status', 'camera_position', 'started_at']
    search_fields = ['vehicle__license_plate']
    readonly_fields = ['started_at']
    ordering = ['-started_at']


@admin.register(VideoArchive)
class VideoArchiveAdmin(admin.ModelAdmin):
    """Admin interface for VideoArchive model."""

    list_display = ['vehicle', 'camera_position', 'duration', 'size', 'created_at', 'retention_until']
    list_filter = ['camera_position', 'created_at']
    search_fields = ['vehicle__license_plate', 'tags']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
