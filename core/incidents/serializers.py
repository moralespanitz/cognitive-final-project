"""
Serializers for incidents app.
"""

from rest_framework import serializers
from .models import Incident, Alert
from video.serializers import VideoArchiveListSerializer


class IncidentSerializer(serializers.ModelSerializer):
    """Serializer for Incident model."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)
    driver_name = serializers.SerializerMethodField()
    video_clips = VideoArchiveListSerializer(many=True, read_only=True)
    video_clip_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Incident
        fields = [
            'id', 'vehicle', 'vehicle_plate', 'driver', 'driver_name',
            'type', 'severity', 'description', 'ai_summary', 'location',
            'video_clips', 'video_clip_ids', 'detected_at', 'resolved_at',
            'resolved_by', 'resolution_notes'
        ]
        read_only_fields = ['id', 'detected_at']

    def get_driver_name(self, obj):
        return obj.driver.user.get_full_name() or obj.driver.user.username

    def create(self, validated_data):
        video_clip_ids = validated_data.pop('video_clip_ids', [])
        incident = Incident.objects.create(**validated_data)
        if video_clip_ids:
            incident.video_clips.set(video_clip_ids)
        return incident


class IncidentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for incident lists."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'vehicle_plate', 'type', 'severity',
            'detected_at', 'resolved_at'
        ]


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)
    incident_details = IncidentListSerializer(source='incident', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'incident', 'incident_details', 'vehicle', 'vehicle_plate',
            'type', 'priority', 'message', 'acknowledged',
            'acknowledged_by', 'acknowledged_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AlertListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for alert lists."""

    vehicle_plate = serializers.CharField(source='vehicle.license_plate', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'vehicle_plate', 'type', 'priority',
            'acknowledged', 'created_at'
        ]


class AlertAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging alerts."""

    acknowledged = serializers.BooleanField(default=True)
