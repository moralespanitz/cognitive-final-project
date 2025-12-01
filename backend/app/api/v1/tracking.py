"""
GPS Tracking API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import List

from ...database import get_db
from ...models.tracking import GPSLocation
from ...models.vehicle import Vehicle
from ...schemas.tracking import GPSLocationCreate, GPSLocationResponse
from ...dependencies import get_current_user
from ...models.user import User
from ...websocket.tracking import broadcast_location_update

router = APIRouter()


@router.post("/location", response_model=GPSLocationResponse, status_code=201)
async def receive_gps_location(
    location_data: GPSLocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive GPS location from device (ESP32).
    No authentication required for devices.
    """
    # Verify vehicle exists
    stmt = select(Vehicle).where(Vehicle.id == location_data.vehicle_id)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Create GPS location
    db_location = GPSLocation(
        vehicle_id=location_data.vehicle_id,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        speed=location_data.speed,
        heading=location_data.heading,
        accuracy=location_data.accuracy,
        altitude=location_data.altitude,
        device_id=location_data.device_id,
        timestamp=datetime.utcnow()
    )

    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)

    # Broadcast to WebSocket clients
    await broadcast_location_update({
        "id": db_location.id,
        "vehicle_id": db_location.vehicle_id,
        "latitude": float(db_location.latitude),
        "longitude": float(db_location.longitude),
        "speed": float(db_location.speed) if db_location.speed else None,
        "heading": float(db_location.heading) if db_location.heading else None,
        "timestamp": db_location.timestamp.isoformat()
    })

    return db_location


@router.get("/live", response_model=List[GPSLocationResponse])
async def get_live_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get latest GPS locations for all active vehicles."""
    # Get latest location for each vehicle (last 60 seconds)
    cutoff_time = datetime.utcnow() - timedelta(seconds=60)

    # Subquery to get latest timestamp per vehicle
    from sqlalchemy import func
    subq = (
        select(
            GPSLocation.vehicle_id,
            func.max(GPSLocation.timestamp).label('max_timestamp')
        )
        .where(GPSLocation.timestamp >= cutoff_time)
        .group_by(GPSLocation.vehicle_id)
        .subquery()
    )

    # Get full location records
    stmt = (
        select(GPSLocation)
        .join(
            subq,
            (GPSLocation.vehicle_id == subq.c.vehicle_id) &
            (GPSLocation.timestamp == subq.c.max_timestamp)
        )
        .order_by(desc(GPSLocation.timestamp))
    )

    result = await db.execute(stmt)
    locations = result.scalars().all()

    return locations


@router.get("/vehicle/{vehicle_id}/history", response_model=List[GPSLocationResponse])
async def get_vehicle_location_history(
    vehicle_id: int,
    hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get GPS location history for a specific vehicle."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    stmt = (
        select(GPSLocation)
        .where(
            GPSLocation.vehicle_id == vehicle_id,
            GPSLocation.timestamp >= cutoff_time
        )
        .order_by(desc(GPSLocation.timestamp))
        .limit(1000)  # Max 1000 points
    )

    result = await db.execute(stmt)
    locations = result.scalars().all()

    return locations
