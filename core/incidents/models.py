from django.db import models
from django.conf import settings
from vehicles.models import Vehicle, Driver
from video.models import VideoArchive


class Incident(models.Model):
    """
    Incident model for tracking safety incidents and events.
    """

    class IncidentType(models.TextChoices):
        ACCIDENT = 'ACCIDENT', 'Accident'
        HARSH_BRAKING = 'HARSH_BRAKING', 'Harsh Braking'
        SPEEDING = 'SPEEDING', 'Speeding'
        AGGRESSIVE_DRIVING = 'AGGRESSIVE_DRIVING', 'Aggressive Driving'
        DROWSINESS = 'DROWSINESS', 'Driver Drowsiness'
        DISTRACTION = 'DISTRACTION', 'Driver Distraction'
        PHONE_USAGE = 'PHONE_USAGE', 'Phone Usage While Driving'
        OTHER = 'OTHER', 'Other'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    type = models.CharField(
        max_length=30,
        choices=IncidentType.choices
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    description = models.TextField(
        help_text='Detailed description of the incident'
    )
    ai_summary = models.TextField(
        blank=True,
        null=True,
        help_text='AI-generated summary of the incident'
    )
    location = models.JSONField(
        help_text='Incident location coordinates {lat, lng, address}'
    )
    video_clips = models.ManyToManyField(
        VideoArchive,
        blank=True,
        related_name='incidents',
        help_text='Associated video evidence'
    )
    detected_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the incident was detected'
    )
    resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When the incident was resolved'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_incidents'
    )
    resolution_notes = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'incidents'
        ordering = ['-detected_at']

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.type} - {self.severity} ({self.detected_at})"


class Alert(models.Model):
    """
    Alert model for real-time notifications about incidents and events.
    """

    class Priority(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        HIGH = 'HIGH', 'High'
        MEDIUM = 'MEDIUM', 'Medium'
        LOW = 'LOW', 'Low'

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    type = models.CharField(
        max_length=50,
        help_text='Alert type/category'
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    message = models.TextField(
        help_text='Alert message content'
    )
    acknowledged = models.BooleanField(
        default=False,
        help_text='Whether alert has been acknowledged'
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.priority} - {self.type}"
