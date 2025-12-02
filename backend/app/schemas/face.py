"""Face registration and verification schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FaceRegisterRequest(BaseModel):
    """Schema for registering a face."""
    face_image: str = Field(..., description="Base64 encoded face image")


class FaceVerifyRequest(BaseModel):
    """Schema for verifying a face."""
    user_id: int = Field(..., description="User ID to verify against")
    face_image: str = Field(..., description="Base64 encoded face image to verify")


class FaceSearchRequest(BaseModel):
    """Schema for searching a face in the collection."""
    face_image: str = Field(..., description="Base64 encoded face image to search")


class FaceRegistrationResponse(BaseModel):
    """Schema for face registration response."""
    id: int
    user_id: int
    is_active: bool
    registered_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VerificationResponse(BaseModel):
    """Schema for verification response."""
    is_match: bool
    similarity_score: int = Field(..., ge=0, le=100, description="Similarity score 0-100")
    user_id: Optional[int] = None
    message: str


class VerificationLogResponse(BaseModel):
    """Schema for verification log response."""
    id: int
    user_id: int
    trip_id: Optional[int] = None
    similarity_score: Optional[int] = None
    is_match: bool
    verified_at: datetime

    class Config:
        from_attributes = True


class FaceSettingsRequest(BaseModel):
    """Schema for updating face recognition settings."""
    similarity_threshold: int = Field(..., ge=0, le=100, description="Similarity threshold 0-100")


class FaceSettingsResponse(BaseModel):
    """Schema for face recognition settings response."""
    similarity_threshold: int
    registered_faces_count: int
