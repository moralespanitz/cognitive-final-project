from django.db import models
from django.conf import settings


class Report(models.Model):
    """
    Report model for storing generated reports.
    """

    class ReportType(models.TextChoices):
        FLEET_PERFORMANCE = 'FLEET_PERFORMANCE', 'Fleet Performance'
        DRIVER_PERFORMANCE = 'DRIVER_PERFORMANCE', 'Driver Performance'
        SAFETY_INCIDENT = 'SAFETY_INCIDENT', 'Safety & Incident'
        ROUTE_ANALYSIS = 'ROUTE_ANALYSIS', 'Route Analysis'
        VEHICLE_MAINTENANCE = 'VEHICLE_MAINTENANCE', 'Vehicle Maintenance'
        AI_INSIGHTS = 'AI_INSIGHTS', 'AI Insights'
        CUSTOM = 'CUSTOM', 'Custom'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        GENERATING = 'GENERATING', 'Generating'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    type = models.CharField(
        max_length=30,
        choices=ReportType.choices
    )
    title = models.CharField(
        max_length=200,
        help_text='Report title'
    )
    parameters = models.JSONField(
        help_text='Report parameters (date range, filters, etc.)'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Path to generated report file'
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Date when report will be automatically deleted'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Error message if report generation failed'
    )

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_type_display()} ({self.status})"
