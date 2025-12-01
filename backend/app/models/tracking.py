"""
GPS tracking model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class GPSLocation(Base):
    """GPS Location model for tracking vehicle positions."""

    __tablename__ = "gps_locations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    speed = Column(Numeric(6, 2), default=0.00)  # km/h
    heading = Column(Integer, default=0)  # degrees (0-359)
    accuracy = Column(Numeric(6, 2))  # meters
    altitude = Column(Numeric(8, 2))  # meters
    device_id = Column(String(50))  # ESP32 device identifier
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, server_default=func.now())

    # Relationships
    vehicle = relationship("Vehicle", back_populates="gps_locations")

    def __repr__(self) -> str:
        return f"<GPSLocation(id={self.id}, vehicle_id={self.vehicle_id}, lat={self.latitude}, lng={self.longitude})>"
