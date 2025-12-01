"""Video schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..models.video import VideoStreamStatus, CameraPosition


class VideoStreamBase(BaseModel):
    """Base video stream schema."""
    vehicle_id: int
    camera_position: CameraPosition = CameraPosition.FRONT


class VideoStreamCreate(VideoStreamBase):
    """Schema for creating a video stream."""
    stream_url: Optional[str] = None


class VideoStreamResponse(VideoStreamBase):
    """Schema for video stream response."""
    id: int
    stream_url: Optional[str] = None
    status: VideoStreamStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoArchiveBase(BaseModel):
    """Base video archive schema."""
    vehicle_id: int
    camera_position: CameraPosition = CameraPosition.FRONT


class VideoArchiveCreate(VideoArchiveBase):
    """Schema for creating a video archive."""
    file_path: str
    file_url: Optional[str] = None
    duration: int = 0
    file_size: int = 0
    metadata: Optional[dict] = None


class VideoArchiveResponse(VideoArchiveBase):
    """Schema for video archive response."""
    id: int
    file_path: str
    file_url: Optional[str] = None
    duration: int
    file_size: int
    thumbnail_url: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    retention_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class FrameUpload(BaseModel):
    """Schema for uploading a frame from ESP32."""
    device_id: str
    vehicle_id: int
    camera_position: CameraPosition = CameraPosition.FRONT
    frame_base64: str  # Base64 encoded image
