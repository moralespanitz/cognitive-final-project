"""
Admin audit log model for tracking administrative actions.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class LogLevel(str, enum.Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionType(str, enum.Enum):
    """Action type enumeration for audit trail."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    SYSTEM = "SYSTEM"


class AdminLog(Base):
    """Admin audit log model for tracking all administrative actions."""

    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)

    # User who performed the action (nullable for system actions)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username = Column(String(50), nullable=True)  # Cached for when user is deleted

    # Action details
    action = Column(SQLEnum(ActionType), nullable=False, index=True)
    level = Column(SQLEnum(LogLevel), default=LogLevel.INFO, nullable=False, index=True)

    # Resource information
    resource_type = Column(String(50), nullable=True, index=True)  # e.g., "user", "vehicle", "trip"
    resource_id = Column(Integer, nullable=True)

    # Description and metadata
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Additional context as JSON

    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", backref="admin_logs")

    def __repr__(self) -> str:
        return f"<AdminLog(id={self.id}, action='{self.action}', user='{self.username}')>"


class SystemMetric(Base):
    """System metrics model for tracking performance and usage statistics."""

    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram

    # Values
    value = Column(String(255), nullable=False)  # String to support various types
    unit = Column(String(50), nullable=True)  # e.g., "requests", "seconds", "bytes"

    # Context
    tags = Column(JSON, nullable=True)  # Additional labels/tags

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<SystemMetric(id={self.id}, name='{self.metric_name}', value='{self.value}')>"
