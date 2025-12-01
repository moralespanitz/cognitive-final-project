"""
Video streaming and archive models.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, BigInteger, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class VideoStreamStatus(str, enum.Enum):
    """Video stream status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


class CameraPosition(str, enum.Enum):
    """Camera position enumeration."""
    FRONT = "FRONT"
    CABIN = "CABIN"
    REAR = "REAR"
    SIDE_LEFT = "SIDE_LEFT"
    SIDE_RIGHT = "SIDE_RIGHT"


class VideoStream(Base):
    """Video stream model for live streaming."""

    __tablename__ = "video_streams"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    camera_position = Column(SQLEnum(CameraPosition), default=CameraPosition.FRONT, nullable=False)
    stream_url = Column(String(500))  # RTSP/HLS URL
    status = Column(SQLEnum(VideoStreamStatus), default=VideoStreamStatus.INACTIVE, nullable=False)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vehicle = relationship("Vehicle", back_populates="video_streams")

    def __repr__(self) -> str:
        return f"<VideoStream(id={self.id}, vehicle_id={self.vehicle_id}, position='{self.camera_position}')>"


class VideoArchive(Base):
    """Video archive model for recorded videos and frames."""

    __tablename__ = "video_archives"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    camera_position = Column(SQLEnum(CameraPosition), default=CameraPosition.FRONT, nullable=False)
    file_path = Column(String(500), nullable=False)  # S3 key or local path
    file_url = Column(String(500))  # Presigned URL
    duration = Column(Integer, default=0)  # seconds (0 for single frame)
    file_size = Column(BigInteger, default=0)  # bytes
    thumbnail_url = Column(String(500))
    extra_metadata = Column(JSON)  # Additional metadata (device_id, fps, resolution, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    retention_until = Column(DateTime(timezone=True))  # Auto-delete after this date

    # Relationships
    vehicle = relationship("Vehicle", back_populates="video_archives")
    incidents = relationship("Incident", secondary="incident_video_archives", back_populates="video_clips")

    def __repr__(self) -> str:
        return f"<VideoArchive(id={self.id}, vehicle_id={self.vehicle_id}, file='{self.file_path}')>"
