"""
Device API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ...database import get_db
from ...schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from ...models.device import Device
from ...dependencies import get_current_user
from ...models.user import User

router = APIRouter()


@router.get("/health", status_code=200)
async def devices_health():
    """Device service health check."""
    return {
        "status": "ok",
        "service": "Devices"
    }


@router.get("", response_model=List[DeviceResponse])
async def get_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vehicle_id: int = None
):
    """Get all devices."""
    query = select(Device)

    if vehicle_id:
        query = query.where(Device.vehicle_id == vehicle_id)

    result = await db.execute(query)
    devices = result.scalars().all()
    return devices


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new device."""
    # Check if serial number already exists
    existing = await db.execute(
        select(Device).where(Device.serial_number == device.serial_number)
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Device with this serial number already exists")

    db_device = Device(**device.model_dump())
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device by ID."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(device)
    await db.commit()
    return None


@router.post("/{device_id}/ping", response_model=DeviceResponse)
async def ping_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Update device last ping timestamp."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.last_ping = datetime.utcnow()
    device.status = "ONLINE"

    await db.commit()
    await db.refresh(device)
    return device
