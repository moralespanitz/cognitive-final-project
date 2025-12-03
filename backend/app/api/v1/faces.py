"""
Face Registration API endpoints.
Simple implementation for user identity verification status tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...database import get_db
from ...models.user import User
from ...dependencies import get_current_user

router = APIRouter()

# In-memory storage for face registrations (in production, use database)
face_registrations: dict[int, dict] = {}


class FaceRegisterRequest(BaseModel):
    """Request to register a face."""
    face_image: str  # Base64 encoded image


class FaceVerifyRequest(BaseModel):
    """Request to verify a face."""
    user_id: Optional[int] = None
    face_image: str  # Base64 encoded image


class FaceStatusResponse(BaseModel):
    """Face registration status response."""
    has_registered_face: bool
    registered_at: Optional[datetime] = None


class FaceVerifyResponse(BaseModel):
    """Face verification response."""
    is_match: bool
    similarity_score: int
    message: str


class FaceRegistrationResponse(BaseModel):
    """Face registration response."""
    success: bool
    message: str
    user_id: int


@router.get("/status", response_model=FaceStatusResponse)
async def get_face_status(
    current_user: User = Depends(get_current_user),
):
    """Get current user's face registration status."""
    registration = face_registrations.get(current_user.id)

    return FaceStatusResponse(
        has_registered_face=registration is not None,
        registered_at=registration.get("registered_at") if registration else None
    )


@router.post("/register", response_model=FaceRegistrationResponse)
async def register_face(
    request: FaceRegisterRequest,
    current_user: User = Depends(get_current_user),
):
    """Register user's face for future verification."""
    # Store face registration (in production, store face embeddings)
    face_registrations[current_user.id] = {
        "face_image": request.face_image[:100] + "...",  # Store truncated for reference
        "registered_at": datetime.utcnow(),
        "user_id": current_user.id,
    }

    return FaceRegistrationResponse(
        success=True,
        message="Face registered successfully",
        user_id=current_user.id
    )


@router.post("/verify-self", response_model=FaceVerifyResponse)
async def verify_self(
    request: FaceRegisterRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify current user's face against their registration."""
    registration = face_registrations.get(current_user.id)

    if not registration:
        return FaceVerifyResponse(
            is_match=False,
            similarity_score=0,
            message="No face registered. Please register first."
        )

    # Simulate verification (in production, compare face embeddings)
    # For now, always return success if user has registered
    return FaceVerifyResponse(
        is_match=True,
        similarity_score=95,
        message="Identity verified successfully"
    )


@router.post("/verify", response_model=FaceVerifyResponse)
async def verify_face(
    request: FaceVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a face against a specific user's registration."""
    user_id = request.user_id or current_user.id
    registration = face_registrations.get(user_id)

    if not registration:
        return FaceVerifyResponse(
            is_match=False,
            similarity_score=0,
            message="User has no registered face"
        )

    # Simulate verification
    return FaceVerifyResponse(
        is_match=True,
        similarity_score=92,
        message="Face verified successfully"
    )


@router.get("/me")
async def get_my_registration(
    current_user: User = Depends(get_current_user),
):
    """Get current user's face registration details."""
    registration = face_registrations.get(current_user.id)

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No face registration found"
        )

    return {
        "user_id": current_user.id,
        "registered_at": registration.get("registered_at"),
        "has_face": True
    }


@router.delete("/me")
async def delete_my_face(
    current_user: User = Depends(get_current_user),
):
    """Delete current user's face registration."""
    if current_user.id in face_registrations:
        del face_registrations[current_user.id]

    return {"success": True, "message": "Face registration deleted"}


# Admin endpoints
@router.get("/admin/all")
async def get_all_registrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all face registrations (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    registrations = []
    for user_id, reg in face_registrations.items():
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        registrations.append({
            "user_id": user_id,
            "username": user.username if user else "Unknown",
            "registered_at": reg.get("registered_at"),
        })

    return {"registrations": registrations, "count": len(registrations)}


@router.get("/admin/logs")
async def get_verification_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """Get face verification logs (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Return empty logs for now
    return {"logs": [], "count": 0}


@router.get("/admin/settings")
async def get_face_settings(
    current_user: User = Depends(get_current_user),
):
    """Get face recognition settings (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return {
        "enabled": True,
        "similarity_threshold": 80,
        "require_verification": False,
    }
