from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin interface for Report model."""

    list_display = ['title', 'type', 'status', 'generated_by', 'created_at', 'completed_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['title', 'generated_by__username']
    readonly_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
