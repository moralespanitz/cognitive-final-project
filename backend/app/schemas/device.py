"""
Device schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..models.device import DeviceType, DeviceStatus


class DeviceBase(BaseModel):
    """Base device schema."""
    vehicle_id: int
    device_type: DeviceType
    serial_number: str
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    config: Optional[dict] = Field(default_factory=dict)


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    status: Optional[DeviceStatus] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    config: Optional[dict] = None
    last_ping: Optional[datetime] = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""
    id: int
    status: DeviceStatus
    last_ping: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
