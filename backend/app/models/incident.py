"""
Incident, Alert, and ChatHistory models.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid
from ..database import Base


class IncidentType(str, enum.Enum):
    """Incident type enumeration."""
    ACCIDENT = "ACCIDENT"
    HARSH_BRAKING = "HARSH_BRAKING"
    SPEEDING = "SPEEDING"
    AGGRESSIVE_DRIVING = "AGGRESSIVE_DRIVING"
    DROWSINESS = "DROWSINESS"
    DISTRACTION = "DISTRACTION"
    PHONE_USAGE = "PHONE_USAGE"
    OTHER = "OTHER"


class IncidentSeverity(str, enum.Enum):
    """Incident severity enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertPriority(str, enum.Enum):
    """Alert priority enumeration."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Association table for many-to-many relationship between Incident and VideoArchive
incident_video_archives = Table(
    'incident_video_archives',
    Base.metadata,
    Column('incident_id', Integer, ForeignKey('incidents.id', ondelete='CASCADE'), primary_key=True),
    Column('video_archive_id', Integer, ForeignKey('video_archives.id', ondelete='CASCADE'), primary_key=True)
)


class Incident(Base):
    """Incident model for tracking safety incidents."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum(IncidentType), nullable=False)
    severity = Column(SQLEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False)
    description = Column(Text, nullable=False)
    ai_summary = Column(Text)  # AI-generated summary
    ai_confidence = Column(Integer)  # 0-100
    location = Column(JSON, nullable=False)  # {lat, lng, address}
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    resolution_notes = Column(Text)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="incidents")
    driver = relationship("Driver", back_populates="incidents")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], back_populates="resolved_incidents")
    video_clips = relationship("VideoArchive", secondary=incident_video_archives, back_populates="incidents")
    alerts = relationship("Alert", back_populates="incident")

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, type='{self.type}', severity='{self.severity}')>"


class Alert(Base):
    """Alert model for real-time notifications."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    priority = Column(SQLEnum(AlertPriority), default=AlertPriority.MEDIUM, nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    incident = relationship("Incident", back_populates="alerts")
    vehicle = relationship("Vehicle", back_populates="alerts")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id], back_populates="acknowledged_alerts")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type='{self.type}', priority='{self.priority}')>"


class ChatHistory(Base):
    """Chat history model for chatbot conversations."""

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="chat_history")

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, session='{self.session_id[:8]}...')>"
