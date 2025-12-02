"""
Face registration and verification API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...database import get_db
from ...models.face import FaceRegistration, VerificationLog
from ...models.user import User
from ...schemas.face import (
    FaceRegisterRequest,
    FaceVerifyRequest,
    FaceSearchRequest,
    FaceRegistrationResponse,
    VerificationResponse,
    VerificationLogResponse,
    FaceSettingsRequest,
    FaceSettingsResponse,
)
from ...services.face_recognition_service import face_recognition_service, FaceRecognitionService
from ...dependencies import get_current_user, get_current_manager_user

router = APIRouter()


@router.post("/register", response_model=FaceRegistrationResponse, status_code=201)
async def register_face(
    request: FaceRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a face for the current user.
    Stores the face image and registers it with the face recognition service.
    """
    # Check if user already has a registered face
    stmt = select(FaceRegistration).where(FaceRegistration.user_id == current_user.id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing registration
        existing.face_data = request.face_image
        existing.is_active = True
        # Re-register with service
        face_recognition_service.register_face(current_user.id, request.face_image)
        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new registration
    db_registration = FaceRegistration(
        user_id=current_user.id,
        face_data=request.face_image,
        is_active=True
    )

    # Register with face recognition service
    face_recognition_service.register_face(current_user.id, request.face_image)

    db.add(db_registration)
    await db.commit()
    await db.refresh(db_registration)

    return db_registration


@router.post("/verify", response_model=VerificationResponse)
async def verify_face(
    request: FaceVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify a face against a registered user.
    Returns match status and similarity score.
    """
    # Verify using the service
    result = face_recognition_service.verify_face(request.user_id, request.face_image)

    # Log the verification attempt
    verification_log = VerificationLog(
        user_id=request.user_id,
        verification_image=request.face_image[:100],  # Store truncated for privacy
        similarity_score=result.similarity_score,
        is_match=result.is_match
    )
    db.add(verification_log)
    await db.commit()

    return VerificationResponse(
        is_match=result.is_match,
        similarity_score=result.similarity_score,
        user_id=result.user_id,
        message=result.message
    )


@router.post("/verify-self", response_model=VerificationResponse)
async def verify_self(
    request: FaceRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify the current user's face against their registered face.
    Convenient endpoint for self-verification before booking.
    """
    # Verify using the service
    result = face_recognition_service.verify_face(current_user.id, request.face_image)

    # Log the verification attempt
    verification_log = VerificationLog(
        user_id=current_user.id,
        verification_image=request.face_image[:100],
        similarity_score=result.similarity_score,
        is_match=result.is_match
    )
    db.add(verification_log)
    await db.commit()

    return VerificationResponse(
        is_match=result.is_match,
        similarity_score=result.similarity_score,
        user_id=current_user.id,
        message=result.message
    )


@router.post("/search", response_model=VerificationResponse)
async def search_face(
    request: FaceSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)  # Admin only
):
    """
    Search for a matching face in the collection.
    Admin only - useful for identifying unknown faces.
    """
    result = face_recognition_service.search_face(request.face_image)

    if result is None:
        return VerificationResponse(
            is_match=False,
            similarity_score=0,
            user_id=None,
            message="No matching face found in collection"
        )

    return VerificationResponse(
        is_match=result.is_match,
        similarity_score=result.similarity_score,
        user_id=result.user_id,
        message=result.message
    )


@router.get("/me", response_model=FaceRegistrationResponse)
async def get_my_face_registration(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's face registration status."""
    stmt = select(FaceRegistration).where(FaceRegistration.user_id == current_user.id)
    result = await db.execute(stmt)
    registration = result.scalar_one_or_none()

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No face registration found"
        )

    return registration


@router.get("/status")
async def get_face_status(
    current_user: User = Depends(get_current_user)
):
    """Quick check if current user has a registered face."""
    has_face = face_recognition_service.has_registered_face(current_user.id)
    return {
        "user_id": current_user.id,
        "has_registered_face": has_face
    }


@router.delete("/me", status_code=204)
async def delete_my_face(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete the current user's face registration."""
    stmt = select(FaceRegistration).where(FaceRegistration.user_id == current_user.id)
    result = await db.execute(stmt)
    registration = result.scalar_one_or_none()

    if registration:
        await db.delete(registration)
        await db.commit()

    # Remove from service
    face_recognition_service.delete_face(current_user.id)

    return None


# Admin endpoints
@router.get("/admin/all", response_model=List[FaceRegistrationResponse])
async def get_all_face_registrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Get all face registrations. Admin only."""
    stmt = select(FaceRegistration).order_by(FaceRegistration.registered_at.desc())
    result = await db.execute(stmt)
    registrations = result.scalars().all()
    return registrations


@router.get("/admin/logs", response_model=List[VerificationLogResponse])
async def get_verification_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Get recent verification logs. Admin only."""
    stmt = (
        select(VerificationLog)
        .order_by(VerificationLog.verified_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs


@router.get("/admin/settings", response_model=FaceSettingsResponse)
async def get_face_settings(
    current_user: User = Depends(get_current_manager_user)
):
    """Get face recognition settings. Admin only."""
    return FaceSettingsResponse(
        similarity_threshold=FaceRecognitionService.get_similarity_threshold(),
        registered_faces_count=FaceRecognitionService.get_collection_count()
    )


@router.put("/admin/settings", response_model=FaceSettingsResponse)
async def update_face_settings(
    request: FaceSettingsRequest,
    current_user: User = Depends(get_current_manager_user)
):
    """Update face recognition settings. Admin only."""
    FaceRecognitionService.set_similarity_threshold(request.similarity_threshold)

    return FaceSettingsResponse(
        similarity_threshold=FaceRecognitionService.get_similarity_threshold(),
        registered_faces_count=FaceRecognitionService.get_collection_count()
    )


@router.delete("/admin/{user_id}", status_code=204)
async def admin_delete_face(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_user)
):
    """Delete a user's face registration. Admin only."""
    stmt = select(FaceRegistration).where(FaceRegistration.user_id == user_id)
    result = await db.execute(stmt)
    registration = result.scalar_one_or_none()

    if registration:
        await db.delete(registration)
        await db.commit()

    face_recognition_service.delete_face(user_id)

    return None
