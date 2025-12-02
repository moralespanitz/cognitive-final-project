"""
Trip image model for storing captured images during trips.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class TripImage(Base):
    """Trip image model for storing images captured during a trip."""

    __tablename__ = "trip_images"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100))  # ESP32-CAM device identifier
    image_data = Column(Text, nullable=False)  # Base64 encoded image
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    trip = relationship("Trip", backref="images")

    def __repr__(self) -> str:
        return f"<TripImage(id={self.id}, trip_id={self.trip_id}, captured_at={self.captured_at})>"
