"""
Vehicles, Drivers, and Trips API endpoints.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...database import get_db
from ...models.user import User
from ...models.vehicle import Vehicle, Driver, Trip
from ...schemas.vehicle import (
    VehicleCreate, VehicleUpdate, VehicleResponse,
    DriverCreate, DriverUpdate, DriverResponse,
    TripCreate, TripUpdate, TripResponse, TripRequest
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


@router.delete("/vehicles/{vehicle_id}", status_code=204)
async def delete_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Delete vehicle."""
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise NotFoundException(detail="Vehicle not found")

    await db.delete(vehicle)
    await db.commit()


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


@router.get("/drivers/me", response_model=DriverResponse)
async def get_my_driver_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's driver profile."""
    stmt = select(Driver).where(Driver.user_id == current_user.id)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        raise NotFoundException(detail="Driver profile not found for current user")

    return driver


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


@router.patch("/drivers/{driver_id}/status", response_model=DriverResponse)
async def update_driver_status(
    driver_id: int,
    driver_status: str = Query(..., description="Driver status: ON_DUTY, OFF_DUTY, or BUSY"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update driver status (ON_DUTY, OFF_DUTY, BUSY)."""
    stmt = select(Driver).where(Driver.id == driver_id)
    result = await db.execute(stmt)
    driver = result.scalar_one_or_none()

    if not driver:
        raise NotFoundException(detail="Driver not found")

    # Only the driver themselves can update their status
    if driver.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this driver's status"
        )

    # Validate status
    valid_statuses = ["ON_DUTY", "OFF_DUTY", "BUSY"]
    if driver_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    driver.status = driver_status
    await db.commit()
    await db.refresh(driver)

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


# Booking Flow Endpoints
@router.post("/trips/request", response_model=TripResponse, status_code=201)
async def request_trip(
    trip_request: TripRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Customer requests a taxi (finds nearest available driver)."""
    from ...models.tracking import GPSLocation
    from ...websocket.trips import trip_manager
    from sqlalchemy import func
    import math

    # Calculate distance between two coordinates
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    # Find available drivers with recent GPS data
    stmt = select(Driver, Vehicle, GPSLocation).join(
        Vehicle, Driver.id == Vehicle.current_driver_id
    ).join(
        GPSLocation, Vehicle.id == GPSLocation.vehicle_id
    ).where(
        Driver.status == "ON_DUTY"
    ).order_by(GPSLocation.timestamp.desc())

    result = await db.execute(stmt)
    available = result.all()

    if not available:
        raise NotFoundException(detail="No available drivers")

    # Find nearest driver
    pickup_lat = trip_request.pickup_location["lat"]
    pickup_lng = trip_request.pickup_location["lng"]

    nearest = min(available, key=lambda x: haversine(
        pickup_lat, pickup_lng, float(x[2].latitude), float(x[2].longitude)
    ))

    driver, vehicle, gps = nearest

    # Calculate estimated fare (simple: $2 base + $1.50/km)
    dest_lat = trip_request.destination["lat"]
    dest_lng = trip_request.destination["lng"]
    distance = haversine(pickup_lat, pickup_lng, dest_lat, dest_lng)
    estimated_fare = 2.0 + (distance * 1.5)

    # Identity verification disabled
    identity_verified = False
    verification_score = None

    # Create trip
    trip = Trip(
        customer_id=current_user.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        pickup_location=trip_request.pickup_location,
        destination=trip_request.destination,
        status="REQUESTED",
        estimated_fare=estimated_fare,
        distance=distance,
        identity_verified=identity_verified,
        verification_score=verification_score
    )

    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    # Broadcast new trip to all connected drivers via WebSocket
    trip_data = {
        "id": trip.id,
        "customer_id": trip.customer_id,
        "vehicle_id": trip.vehicle_id,
        "driver_id": trip.driver_id,
        "pickup_location": trip.pickup_location,
        "destination": trip.destination,
        "status": trip.status,
        "estimated_fare": float(trip.estimated_fare) if trip.estimated_fare else 0,
        "distance": float(trip.distance) if trip.distance else 0,
        "identity_verified": trip.identity_verified,
        "verification_score": trip.verification_score,
        "created_at": trip.created_at.isoformat() if trip.created_at else None
    }
    await trip_manager.broadcast_new_trip(trip_data)

    return trip


@router.post("/trips/{trip_id}/accept", response_model=TripResponse)
async def accept_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Driver accepts a trip."""
    from ...websocket.trips import trip_manager

    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise NotFoundException(detail="Trip not found")

    trip.status = "ACCEPTED"
    await db.commit()
    await db.refresh(trip)

    # Notify customer and other drivers via WebSocket
    trip_data = {
        "id": trip.id,
        "customer_id": trip.customer_id,
        "vehicle_id": trip.vehicle_id,
        "driver_id": trip.driver_id,
        "pickup_location": trip.pickup_location,
        "destination": trip.destination,
        "status": trip.status,
        "estimated_fare": float(trip.estimated_fare) if trip.estimated_fare else 0,
        "distance": float(trip.distance) if trip.distance else 0,
    }
    await trip_manager.notify_trip_accepted(trip_data)

    return trip


@router.post("/trips/{trip_id}/arrive", response_model=TripResponse)
async def arrive_at_pickup(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Driver arrived at pickup location."""
    from ...websocket.trips import trip_manager

    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise NotFoundException(detail="Trip not found")

    trip.status = "ARRIVED"
    await db.commit()
    await db.refresh(trip)

    # Notify customer via WebSocket
    trip_data = {
        "id": trip.id,
        "customer_id": trip.customer_id,
        "vehicle_id": trip.vehicle_id,
        "driver_id": trip.driver_id,
        "status": trip.status,
    }
    await trip_manager.notify_trip_update(trip.id, trip_data, "driver_arrived")

    return trip


@router.post("/trips/{trip_id}/start", response_model=TripResponse)
async def start_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start the trip (passenger onboard)."""
    from datetime import datetime, timezone
    from ...websocket.trips import trip_manager

    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise NotFoundException(detail="Trip not found")

    trip.status = "IN_PROGRESS"
    trip.start_time = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(trip)

    # Notify customer via WebSocket - trip started, show live camera
    trip_data = {
        "id": trip.id,
        "customer_id": trip.customer_id,
        "vehicle_id": trip.vehicle_id,
        "driver_id": trip.driver_id,
        "status": trip.status,
        "start_time": trip.start_time.isoformat() if trip.start_time else None,
    }
    await trip_manager.notify_trip_update(trip.id, trip_data, "trip_started")

    return trip


@router.post("/trips/{trip_id}/complete", response_model=TripResponse)
async def complete_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete the trip."""
    from datetime import datetime, timezone
    from ...websocket.trips import trip_manager

    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise NotFoundException(detail="Trip not found")

    now = datetime.now(timezone.utc)
    trip.status = "COMPLETED"
    trip.end_time = now
    trip.fare = trip.estimated_fare  # In production, calculate actual fare

    if trip.start_time:
        duration = (now - trip.start_time).total_seconds() / 60
        trip.duration = int(duration)

    await db.commit()
    await db.refresh(trip)

    # Notify customer via WebSocket - trip completed
    trip_data = {
        "id": trip.id,
        "customer_id": trip.customer_id,
        "vehicle_id": trip.vehicle_id,
        "driver_id": trip.driver_id,
        "status": trip.status,
        "fare": float(trip.fare) if trip.fare else 0,
        "duration": trip.duration,
    }
    await trip_manager.notify_trip_update(trip.id, trip_data, "trip_completed")

    return trip


@router.post("/trips/{trip_id}/cancel", response_model=TripResponse)
async def cancel_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a trip."""
    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise NotFoundException(detail="Trip not found")

    trip.status = "CANCELLED"
    await db.commit()
    await db.refresh(trip)

    return trip


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trip details."""
    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise NotFoundException(detail="Trip not found")

    return trip


@router.get("/drivers/available", response_model=List[DriverResponse])
async def get_available_drivers(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(5.0),  # km
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available drivers near a location."""
    from ...models.tracking import GPSLocation

    stmt = select(Driver).join(
        Vehicle, Driver.id == Vehicle.current_driver_id
    ).where(Driver.status == "ON_DUTY")

    result = await db.execute(stmt)
    drivers = result.scalars().all()

    return drivers
