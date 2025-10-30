"""
Serializers for video app.
"""

from rest_framework import serializers
from .models import VideoStream, VideoArchive


class VideoStreamSerializer(serializers.ModelSerializer):
    """Serializer for VideoStream model."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)

    class Meta:
        model = VideoStream
        fields = [
            'id', 'vehicle', 'vehicle_plate', 'camera_position',
            'stream_url', 'recording_url', 'status',
            'started_at', 'ended_at'
        ]
        read_only_fields = ['id', 'started_at']


class VideoStreamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating video streams."""

    class Meta:
        model = VideoStream
        fields = ['vehicle', 'camera_position', 'stream_url']


class VideoArchiveSerializer(serializers.ModelSerializer):
    """Serializer for VideoArchive model."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)

    class Meta:
        model = VideoArchive
        fields = [
            'id', 'vehicle', 'vehicle_plate', 'file_path', 'duration',
            'size', 'tags', 'thumbnail', 'camera_position',
            'created_at', 'retention_until'
        ]
        read_only_fields = ['id', 'created_at']


class VideoArchiveListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for video archive lists."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)

    class Meta:
        model = VideoArchive
        fields = [
            'id', 'vehicle_plate', 'camera_position', 'duration',
            'thumbnail', 'created_at'
        ]
