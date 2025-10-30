from django.db import models
from vehicles.models import Vehicle


class VideoStream(models.Model):
    """
    Video Stream model for managing live video feeds from vehicles.
    """

    class Status(models.TextChoices):
        STARTING = 'STARTING', 'Starting'
        ACTIVE = 'ACTIVE', 'Active'
        STOPPED = 'STOPPED', 'Stopped'
        ERROR = 'ERROR', 'Error'

    class CameraPosition(models.TextChoices):
        FRONT = 'FRONT', 'Front Camera'
        CABIN = 'CABIN', 'Cabin Camera'
        REAR = 'REAR', 'Rear Camera'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='video_streams'
    )
    camera_position = models.CharField(
        max_length=20,
        choices=CameraPosition.choices,
        default=CameraPosition.FRONT
    )
    stream_url = models.URLField(
        max_length=500,
        help_text='URL for live stream'
    )
    recording_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='URL for recorded video'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STARTING
    )
    started_at = models.DateTimeField(
        auto_now_add=True
    )
    ended_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'video_streams'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.camera_position} - {self.status}"


class VideoArchive(models.Model):
    """
    Video Archive model for storing recorded video files.
    """

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='video_archives'
    )
    file_path = models.CharField(
        max_length=500,
        help_text='Path to video file (S3 or local)'
    )
    duration = models.IntegerField(
        default=0,
        help_text='Video duration in seconds'
    )
    size = models.BigIntegerField(
        default=0,
        help_text='File size in bytes'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Tags for categorization and search'
    )
    thumbnail = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Path to thumbnail image'
    )
    camera_position = models.CharField(
        max_length=20,
        choices=VideoStream.CameraPosition.choices,
        default=VideoStream.CameraPosition.FRONT
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    retention_until = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Date when video will be automatically deleted'
    )

    class Meta:
        db_table = 'video_archives'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
