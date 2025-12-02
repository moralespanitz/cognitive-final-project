"""
Trip images API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime

from ...database import get_db
from ...models.image import TripImage
from ...models.vehicle import Trip
from ...models.user import User
from ...schemas.image import (
    TripImageCreate,
    TripImageResponse,
    TripImageListResponse,
    ImageHistoryResponse,
)
from ...dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=TripImageResponse, status_code=201)
async def create_trip_image(
    image: TripImageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new trip image.
    Called by ESP32-CAM devices to store captured images.
    No authentication required for device uploads.
    """
    # Verify trip exists
    stmt = select(Trip).where(Trip.id == image.trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Create image record
    db_image = TripImage(
        trip_id=image.trip_id,
        device_id=image.device_id,
        image_data=image.image_data
    )

    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)

    return db_image


@router.get("/trip/{trip_id}", response_model=TripImageListResponse)
async def get_trip_images(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all images for a specific trip.
    User must be the trip customer or an admin.
    """
    # Get trip to verify access
    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check access (customer or admin)
    if trip.customer_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these images"
        )

    # Get images
    stmt = (
        select(TripImage)
        .where(TripImage.trip_id == trip_id)
        .order_by(TripImage.captured_at.asc())
    )
    result = await db.execute(stmt)
    images = result.scalars().all()

    # Get count
    count_stmt = select(func.count()).select_from(TripImage).where(TripImage.trip_id == trip_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    return TripImageListResponse(
        images=images,
        total=total,
        trip_id=trip_id
    )


@router.get("/history", response_model=ImageHistoryResponse)
async def get_image_history(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get image history for the current user's trips.
    Supports date filtering and pagination.
    """
    # Build query for user's trips
    conditions = [Trip.customer_id == current_user.id]

    if start_date:
        conditions.append(TripImage.captured_at >= start_date)
    if end_date:
        conditions.append(TripImage.captured_at <= end_date)

    # Get images
    stmt = (
        select(TripImage)
        .join(Trip, TripImage.trip_id == Trip.id)
        .where(and_(*conditions))
        .order_by(TripImage.captured_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    images = result.scalars().all()

    # Get total count
    count_stmt = (
        select(func.count())
        .select_from(TripImage)
        .join(Trip, TripImage.trip_id == Trip.id)
        .where(and_(*conditions))
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    return ImageHistoryResponse(
        images=images,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/latest/{trip_id}", response_model=TripImageResponse)
async def get_latest_trip_image(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the latest image for a specific trip.
    Useful for live monitoring.
    """
    # Get trip to verify access
    stmt = select(Trip).where(Trip.id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check access
    if trip.customer_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these images"
        )

    # Get latest image
    stmt = (
        select(TripImage)
        .where(TripImage.trip_id == trip_id)
        .order_by(TripImage.captured_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found for this trip"
        )

    return image


@router.delete("/{image_id}", status_code=204)
async def delete_trip_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a trip image.
    Admin only.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    stmt = select(TripImage).where(TripImage.id == image_id)
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    await db.delete(image)
    await db.commit()

    return None
