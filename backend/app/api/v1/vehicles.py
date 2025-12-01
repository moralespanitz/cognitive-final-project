"""
Vehicles, Drivers, and Trips API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...database import get_db
from ...models.user import User
from ...models.vehicle import Vehicle, Driver, Trip
from ...schemas.vehicle import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    DriverCreate, DriverUpdate, DriverResponse,
    TripCreate, TripUpdate, TripResponse
)
from ...dependencies import get_current_user, get_current_manager_user
from ...core.exceptions import NotFoundException, ConflictException

router = APIRouter()


# Vehicle Endpoints
@router.post("/vehicles", response_model=VehicleResponse, status_code=201)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Create a new vehicle."""
    # Check if license plate exists
    stmt = select(Vehicle).where(Vehicle.license_plate == vehicle_data.license_plate)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException(detail="License plate already registered")

    # Check if VIN exists
    stmt = select(Vehicle).where(Vehicle.vin == vehicle_data.vin)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException(detail="VIN already registered")

    db_vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)

    return db_vehicle


@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all vehicles."""
    stmt = select(Vehicle)

    if status:
        stmt = stmt.where(Vehicle.status == status)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    vehicles = result.scalars().all()

    return vehicles


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vehicle by ID."""
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise NotFoundException(detail="Vehicle not found")

    return vehicle


@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    vehicle_update: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Update vehicle."""
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise NotFoundException(detail="Vehicle not found")

    # Update fields
    update_data = vehicle_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    await db.commit()
    await db.refresh(vehicle)

    return vehicle


# Driver Endpoints
@router.post("/drivers", response_model=DriverResponse, status_code=201)
async def create_driver(
    driver_data: DriverCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Create a new driver."""
    # Check if license number exists
    stmt = select(Driver).where(Driver.license_number == driver_data.license_number)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException(detail="License number already registered")

    # Check if user already has driver profile
    stmt = select(Driver).where(Driver.user_id == driver_data.user_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException(detail="User already has a driver profile")

    db_driver = Driver(**driver_data.model_dump())
    db.add(db_driver)
    await db.commit()
    await db.refresh(db_driver)

    return db_driver


@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all drivers."""
    stmt = select(Driver)

    if status:
        stmt = stmt.where(Driver.status == status)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    drivers = result.scalars().all()

    return drivers


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get driver by ID."""
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        raise NotFoundException(detail="Driver not found")

    return driver


# Trip Endpoints
@router.post("/trips", response_model=TripResponse, status_code=201)
async def create_trip(
    trip_data: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trip."""
    db_trip = Trip(**trip_data.model_dump())
    db.add(db_trip)
    await db.commit()
    await db.refresh(db_trip)

    return db_trip


@router.get("/trips", response_model=List[TripResponse])
async def list_trips(
    skip: int = 0,
    limit: int = 50,
    vehicle_id: int = None,
    driver_id: int = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List trips with optional filters."""
    stmt = select(Trip)

    if vehicle_id:
        stmt = stmt.where(Trip.vehicle_id == vehicle_id)
    if driver_id:
        stmt = stmt.where(Trip.driver_id == driver_id)
    if status:
        stmt = stmt.where(Trip.status == status)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    trips = result.scalars().all()

    return trips
