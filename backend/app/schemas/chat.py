"""
Pydantic schemas for chat/AI interactions.
"""
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Schema for incoming chat message."""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")


class ChatResponse(BaseModel):
    """Schema for chat response."""
    response: str = Field(..., description="AI response")
    message: str = Field(..., description="Original user message")
