from django.db import models
from django.conf import settings


class Driver(models.Model):
    """
    Driver model for managing taxi drivers.
    """

    class Status(models.TextChoices):
        ON_DUTY = 'ON_DUTY', 'On Duty'
        OFF_DUTY = 'OFF_DUTY', 'Off Duty'
        ON_BREAK = 'ON_BREAK', 'On Break'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    license_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Driver license number'
    )
    license_expiry = models.DateField(
        help_text='License expiration date'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFF_DUTY
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text='Average driver rating (0-5)'
    )
    total_trips = models.IntegerField(
        default=0,
        help_text='Total number of completed trips'
    )
    photo = models.ImageField(
        upload_to='drivers/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'drivers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.license_number}"


class Vehicle(models.Model):
    """
    Vehicle model for managing taxi fleet.
    """

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'

    license_plate = models.CharField(
        max_length=20,
        unique=True,
        help_text='Vehicle license plate number'
    )
    make = models.CharField(
        max_length=50,
        help_text='Vehicle manufacturer'
    )
    model = models.CharField(
        max_length=50,
        help_text='Vehicle model'
    )
    year = models.IntegerField(
        help_text='Manufacturing year'
    )
    color = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    vin = models.CharField(
        max_length=17,
        unique=True,
        help_text='Vehicle Identification Number'
    )
    capacity = models.IntegerField(
        default=4,
        help_text='Passenger capacity'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    current_driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicle'
    )
    registration_date = models.DateField(
        blank=True,
        null=True,
        help_text='Vehicle registration date'
    )
    insurance_expiry = models.DateField(
        blank=True,
        null=True,
        help_text='Insurance expiration date'
    )
    last_service_date = models.DateField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license_plate} - {self.make} {self.model}"


class Trip(models.Model):
    """
    Trip model for tracking individual taxi trips.
    """

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='trips'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='trips'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(
        blank=True,
        null=True
    )
    start_location = models.JSONField(
        help_text='Start location coordinates {lat, lng, address}'
    )
    end_location = models.JSONField(
        blank=True,
        null=True,
        help_text='End location coordinates {lat, lng, address}'
    )
    distance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Trip distance in kilometers'
    )
    duration = models.IntegerField(
        default=0,
        help_text='Trip duration in minutes'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Trip fare amount'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trips'
        ordering = ['-start_time']

    def __str__(self):
        return f"Trip {self.id} - {self.vehicle.license_plate} - {self.status}"
