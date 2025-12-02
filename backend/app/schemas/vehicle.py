"""Vehicle, Driver, and Trip schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from ..models.vehicle import DriverStatus, VehicleStatus, TripStatus


# Driver Schemas
class DriverBase(BaseModel):
    """Base driver schema."""
    license_number: str = Field(..., min_length=5, max_length=50)
    license_expiry: date
    status: DriverStatus = DriverStatus.OFF_DUTY


class DriverCreate(DriverBase):
    """Schema for creating a driver."""
    user_id: int


class DriverUpdate(BaseModel):
    """Schema for updating a driver."""
    license_expiry: Optional[date] = None
    status: Optional[DriverStatus] = None
    photo_url: Optional[str] = None


class DriverResponse(DriverBase):
    """Schema for driver response."""
    id: int
    user_id: int
    rating: Decimal
    total_trips: int
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Vehicle Schemas
class VehicleBase(BaseModel):
    """Base vehicle schema."""
    license_plate: str = Field(..., min_length=3, max_length=20)
    make: str = Field(..., max_length=50)
    model: str = Field(..., max_length=50)
    year: int = Field(..., ge=1990, le=2030)
    color: Optional[str] = Field(None, max_length=30)
    vin: str = Field(..., min_length=17, max_length=17)
    capacity: int = Field(default=4, ge=1, le=20)
    status: VehicleStatus = VehicleStatus.ACTIVE


class VehicleCreate(VehicleBase):
    """Schema for creating a vehicle."""
    current_driver_id: Optional[int] = None
    registration_date: Optional[date] = None
    insurance_expiry: Optional[date] = None


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    status: Optional[VehicleStatus] = None
    current_driver_id: Optional[int] = None
    color: Optional[str] = None
    insurance_expiry: Optional[date] = None
    last_service_date: Optional[date] = None


class VehicleResponse(VehicleBase):
    """Schema for vehicle response."""
    id: int
    current_driver_id: Optional[int] = None
    registration_date: Optional[date] = None
    insurance_expiry: Optional[date] = None
    last_service_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Trip Schemas
class TripRequest(BaseModel):
    """Customer trip request."""
    pickup_location: dict  # {lat, lng, address}
    destination: dict  # {lat, lng, address}
    verification_image: Optional[str] = None  # Base64 encoded verification image


class TripBase(BaseModel):
    """Base trip schema."""
    pickup_location: dict
    destination: dict
    status: TripStatus = TripStatus.REQUESTED


class TripCreate(TripBase):
    """Schema for creating a trip."""
    customer_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None


class TripUpdate(BaseModel):
    """Schema for updating a trip."""
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    distance: Optional[Decimal] = None
    duration: Optional[int] = None
    status: Optional[TripStatus] = None
    fare: Optional[Decimal] = None


class TripResponse(BaseModel):
    """Schema for trip response."""
    id: int
    customer_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    pickup_location: dict
    destination: dict
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    distance: Decimal
    duration: int
    status: TripStatus
    fare: Decimal
    estimated_fare: Decimal
    identity_verified: bool = False
    verification_score: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
