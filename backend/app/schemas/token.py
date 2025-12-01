"""Token schemas."""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str  # Subject (user ID or username)
    exp: int  # Expiration time
    type: str  # Token type (access or refresh)


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str
