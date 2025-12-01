"""
Pydantic schemas for GPS tracking.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class GPSLocationCreate(BaseModel):
    """Schema for creating GPS location."""
    vehicle_id: int = Field(..., description="Vehicle ID")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, lt=360, description="Heading in degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS accuracy in meters")
    device_id: Optional[str] = Field(None, max_length=100, description="Device identifier")


class GPSLocationResponse(BaseModel):
    """Schema for GPS location response."""
    id: int
    vehicle_id: int
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    device_id: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
