"""
Video API endpoints.
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request, Header, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import base64
import logging
from datetime import datetime, timedelta

from ...database import get_db
from ...models.user import User
from ...models.video import VideoArchive, VideoStream
from ...models.vehicle import Vehicle
from ...schemas.video import VideoArchiveResponse, FrameUpload
from ...dependencies import get_current_user
from ...core.exceptions import NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# ESP32-CAM DEVICE ENDPOINT - Simple image receiver (no AI)
# ============================================================================

# Store latest frame per device for WebSocket streaming
latest_frames = {}  # {device_id: {"image": base64_string, "timestamp": datetime}}


@router.post("/device/upload")
async def device_upload_image(
    request: Request,
    x_route_id: Optional[str] = Header(None, alias="X-Route-ID"),
):
    """
    Receive raw JPEG image from ESP32-CAM device.
    Stores it for WebSocket streaming to frontend.

    ESP32 sends: Content-Type: image/jpeg with raw bytes
    """
    try:
        image_bytes = await request.body()

        if not image_bytes or len(image_bytes) < 100:
            return JSONResponse(status_code=400, content={"error": "No image"})

        route_id = x_route_id or request.query_params.get("route_id", "taxi-01")

        # Store as base64 for WebSocket streaming
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        latest_frames[route_id] = {
            "image": image_base64,
            "timestamp": datetime.utcnow().isoformat(),
            "size": len(image_bytes)
        }

        logger.info(f"📸 Frame received: {route_id}, {len(image_bytes)} bytes")

        return {"success": True, "route_id": route_id, "size": len(image_bytes)}

    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/device/latest/{route_id}")
async def get_latest_frame(route_id: str):
    """Get the latest frame for a device (for polling fallback)."""
    if route_id in latest_frames:
        return latest_frames[route_id]
    return {"error": "No frame available", "route_id": route_id}


@router.get("/device/list")
async def list_active_devices():
    """List all devices that have sent frames."""
    return {
        "devices": list(latest_frames.keys()),
        "count": len(latest_frames)
    }


# ============================================================================
# FRAME UPLOAD ENDPOINTS (Base64 JSON format)
# ============================================================================

@router.post("/frames/upload", response_model=VideoArchiveResponse, status_code=201)
async def upload_frame(
    frame_data: FrameUpload,
    db: AsyncSession = Depends(get_db)
):
    """Upload video frame from ESP32 (no auth required for devices)."""
    # Verify vehicle exists
    stmt = select(Vehicle).where(Vehicle.id == frame_data.vehicle_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise NotFoundException(detail="Vehicle not found")

    # Decode base64 frame
    try:
        frame_bytes = base64.b64decode(frame_data.frame_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {str(e)}")

    # Generate filename
    timestamp = datetime.utcnow()
    filename = f"frames/vehicle_{frame_data.vehicle_id}/{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"

    # Save to S3 (or local for development)
    # TODO: Implement S3 upload using boto3
    file_path = filename  # S3 key

    # Create archive record
    archive = VideoArchive(
        vehicle_id=frame_data.vehicle_id,
        camera_position=frame_data.camera_position,
        file_path=file_path,
        file_size=len(frame_bytes),
        duration=0,  # Single frame
        metadata={"device_id": frame_data.device_id, "type": "frame"},
        retention_until=timestamp + timedelta(days=7)
    )

    db.add(archive)
    await db.commit()
    await db.refresh(archive)

    # TODO: Enqueue for AI analysis
    # await enqueue_ai_analysis(archive.id)

    return archive


@router.get("/archives", response_model=List[VideoArchiveResponse])
async def list_video_archives(
    skip: int = 0,
    limit: int = 50,
    vehicle_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List video archives."""
    stmt = select(VideoArchive)

    if vehicle_id:
        stmt = stmt.where(VideoArchive.vehicle_id == vehicle_id)

    stmt = stmt.offset(skip).limit(limit).order_by(VideoArchive.created_at.desc())
    result = await db.execute(stmt)
    archives = result.scalars().all()

    return archives


@router.get("/archives/{archive_id}", response_model=VideoArchiveResponse)
async def get_video_archive(
    archive_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get video archive by ID."""
    stmt = select(VideoArchive).where(VideoArchive.id == archive_id)
    result = await db.execute(stmt)
    archive = result.scalar_one_or_none()

    if not archive:
        raise NotFoundException(detail="Video archive not found")

    return archive
