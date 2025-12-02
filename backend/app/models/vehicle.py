"""
Vehicle, Driver, and Trip models.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Date, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class DriverStatus(str, enum.Enum):
    """Driver status enumeration."""
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"
    ON_BREAK = "ON_BREAK"
    SUSPENDED = "SUSPENDED"


class VehicleStatus(str, enum.Enum):
    """Vehicle status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class TripStatus(str, enum.Enum):
    """Trip status enumeration."""
    REQUESTED = "REQUESTED"  # Customer requested, waiting for driver
    ACCEPTED = "ACCEPTED"  # Driver accepted, heading to pickup
    ARRIVED = "ARRIVED"  # Driver at pickup location
    IN_PROGRESS = "IN_PROGRESS"  # Trip started, passenger onboard
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SCHEDULED = "SCHEDULED"  # For pre-scheduled trips


class Driver(Base):
    """Driver model."""

    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    license_expiry = Column(Date, nullable=False)
    status = Column(SQLEnum(DriverStatus), default=DriverStatus.OFF_DUTY, nullable=False)
    rating = Column(Numeric(3, 2), default=0.00)
    total_trips = Column(Integer, default=0)
    photo_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="driver_profile")
    assigned_vehicle = relationship("Vehicle", back_populates="current_driver")
    trips = relationship("Trip", back_populates="driver")
    incidents = relationship("Incident", back_populates="driver")

    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, license='{self.license_number}', status='{self.status}')>"


class Vehicle(Base):
    """Vehicle model."""

    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, nullable=False, index=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(30))
    vin = Column(String(17), unique=True, nullable=False)
    capacity = Column(Integer, default=4)
    status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.ACTIVE, nullable=False)
    current_driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"))
    registration_date = Column(Date)
    insurance_expiry = Column(Date)
    last_service_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    current_driver = relationship("Driver", back_populates="assigned_vehicle")
    trips = relationship("Trip", back_populates="vehicle")
    gps_locations = relationship("GPSLocation", back_populates="vehicle")
    video_streams = relationship("VideoStream", back_populates="vehicle")
    video_archives = relationship("VideoArchive", back_populates="vehicle")
    incidents = relationship("Incident", back_populates="vehicle")
    alerts = relationship("Alert", back_populates="vehicle")
    devices = relationship("Device", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, plate='{self.license_plate}', status='{self.status}')>"


class Trip(Base):
    """Trip model."""

    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"))
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    pickup_location = Column(JSON, nullable=False)  # {lat, lng, address}
    destination = Column(JSON, nullable=False)  # {lat, lng, address}
    distance = Column(Numeric(10, 2), default=0.00)  # kilometers
    duration = Column(Integer, default=0)  # minutes
    status = Column(SQLEnum(TripStatus), default=TripStatus.REQUESTED, nullable=False)
    fare = Column(Numeric(10, 2), default=0.00)
    estimated_fare = Column(Numeric(10, 2), default=0.00)
    identity_verified = Column(Boolean, default=False)  # True if customer verified identity before trip
    verification_score = Column(Integer)  # Similarity score from face verification (0-100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")

    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, vehicle_id={self.vehicle_id}, status='{self.status}')>"
