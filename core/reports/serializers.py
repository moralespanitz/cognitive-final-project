"""
Serializers for reports app.
"""

from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""

    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'type', 'title', 'parameters', 'status', 'file_path',
            'generated_by', 'generated_by_name', 'created_at',
            'completed_at', 'expires_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'created_at',
            'completed_at', 'error_message'
        ]

    def get_generated_by_name(self, obj):
        return obj.generated_by.get_full_name() or obj.generated_by.username


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports."""

    class Meta:
        model = Report
        fields = ['type', 'title', 'parameters']


class ReportListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for report lists."""

    class Meta:
        model = Report
        fields = ['id', 'type', 'title', 'status', 'created_at', 'completed_at']
