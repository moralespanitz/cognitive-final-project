from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    Extends Django's AbstractUser to add additional fields.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        FLEET_MANAGER = 'FLEET_MANAGER', 'Fleet Manager'
        DISPATCHER = 'DISPATCHER', 'Dispatcher'
        OPERATOR = 'OPERATOR', 'Operator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
        help_text='User role for access control'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Contact phone number'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='User profile picture'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_fleet_manager(self):
        return self.role == self.Role.FLEET_MANAGER

    @property
    def is_dispatcher(self):
        return self.role == self.Role.DISPATCHER
