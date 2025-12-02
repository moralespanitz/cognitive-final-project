"""
Face registration model for identity verification.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base


class FaceRegistration(Base):
    """Face registration model for storing user face data."""

    __tablename__ = "face_registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    face_data = Column(Text, nullable=False)  # Base64 encoded image
    face_encoding = Column(Text)  # Simulated face encoding (for mock matching)
    is_active = Column(Boolean, default=True, nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="face_registration")

    def __repr__(self) -> str:
        return f"<FaceRegistration(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class VerificationLog(Base):
    """Log of face verification attempts."""

    __tablename__ = "verification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    verification_image = Column(Text)  # Base64 encoded image used for verification
    similarity_score = Column(Integer)  # 0-100 confidence score
    is_match = Column(Boolean, nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="verification_logs")

    def __repr__(self) -> str:
        return f"<VerificationLog(id={self.id}, user_id={self.user_id}, is_match={self.is_match}, score={self.similarity_score})>"
