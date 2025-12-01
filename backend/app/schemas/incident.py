"""Incident and Alert schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.incident import IncidentType, IncidentSeverity, AlertPriority


# Incident Schemas
class IncidentBase(BaseModel):
    """Base incident schema."""
    vehicle_id: int
    driver_id: int
    type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    description: str
    location: dict  # {lat, lng, address}


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""
    ai_summary: Optional[str] = None
    ai_confidence: Optional[int] = Field(None, ge=0, le=100)


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""
    severity: Optional[IncidentSeverity] = None
    description: Optional[str] = None
    resolution_notes: Optional[str] = None


class IncidentResponse(IncidentBase):
    """Schema for incident response."""
    id: int
    ai_summary: Optional[str] = None
    ai_confidence: Optional[int] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[int] = None
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    """Base alert schema."""
    vehicle_id: int
    type: str
    priority: AlertPriority = AlertPriority.MEDIUM
    message: str


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    incident_id: Optional[int] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    id: int
    incident_id: Optional[int] = None
    acknowledged: bool
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    pass  # No fields needed, user comes from token
