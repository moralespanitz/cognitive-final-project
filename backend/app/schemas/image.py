"""Trip image schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TripImageCreate(BaseModel):
    """Schema for creating a trip image."""
    trip_id: int = Field(..., description="Trip ID")
    device_id: Optional[str] = Field(None, description="Device ID that captured the image")
    image_data: str = Field(..., description="Base64 encoded image data")


class TripImageResponse(BaseModel):
    """Schema for trip image response."""
    id: int
    trip_id: int
    device_id: Optional[str] = None
    image_data: str
    captured_at: datetime

    class Config:
        from_attributes = True


class TripImageListResponse(BaseModel):
    """Schema for listing trip images."""
    images: List[TripImageResponse]
    total: int
    trip_id: int


class ImageHistoryRequest(BaseModel):
    """Schema for requesting image history."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100, description="Max number of images to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class ImageHistoryResponse(BaseModel):
    """Schema for image history response."""
    images: List[TripImageResponse]
    total: int
    limit: int
    offset: int
