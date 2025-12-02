"""
User model with role-based access control.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "ADMIN"
    FLEET_MANAGER = "FLEET_MANAGER"
    DISPATCHER = "DISPATCHER"
    OPERATOR = "OPERATOR"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    driver_profile = relationship("Driver", back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def is_fleet_manager(self) -> bool:
        """Check if user is fleet manager."""
        return self.role == UserRole.FLEET_MANAGER
