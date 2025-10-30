from django.db import models
from vehicles.models import Vehicle


class GPS_Location(models.Model):
    """
    GPS Location model for tracking vehicle positions in real-time.
    Stores time-series location data.
    """

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        help_text='Longitude coordinate'
    )
    speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        help_text='Speed in km/h'
    )
    heading = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='Direction heading in degrees (0-360)'
    )
    accuracy = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        help_text='Location accuracy in meters'
    )
    altitude = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Altitude in meters'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Time when location was recorded'
    )

    class Meta:
        db_table = 'gps_locations'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.vehicle.license_plate} @ {self.latitude}, {self.longitude} ({self.timestamp})"
