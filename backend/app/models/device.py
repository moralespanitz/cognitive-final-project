"""
Device model for hardware tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class DeviceType(str, enum.Enum):
    """Device type enumeration."""
    GPS = "GPS"
    CAMERA = "CAMERA"
    SENSOR = "SENSOR"
    OBD = "OBD"
    OTHER = "OTHER"


class DeviceStatus(str, enum.Enum):
    """Device status enumeration."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class Device(Base):
    """Device model for tracking hardware."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.OFFLINE, nullable=False)

    # Device information
    model = Column(String(100))
    manufacturer = Column(String(100))
    firmware_version = Column(String(50))

    # Connection info
    last_ping = Column(DateTime(timezone=True))
    ip_address = Column(String(45))  # IPv6 compatible

    # Configuration
    config = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    vehicle = relationship("Vehicle", back_populates="devices")

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, type='{self.device_type}', serial='{self.serial_number}', status='{self.status}')>"

    @property
    def is_online(self) -> bool:
        """Check if device is currently online."""
        return self.status == DeviceStatus.ONLINE

    @property
    def needs_maintenance(self) -> bool:
        """Check if device needs maintenance."""
        return self.status == DeviceStatus.MAINTENANCE
