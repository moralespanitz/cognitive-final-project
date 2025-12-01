"""
FAQ schemas.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.faq import FAQCategory


class FAQBase(BaseModel):
    """Base FAQ schema."""
    question: str
    answer: str
    category: FAQCategory = FAQCategory.GENERAL
    keywords: Optional[str] = None
    priority: int = 0


class FAQCreate(FAQBase):
    """Schema for creating FAQ."""
    is_active: bool = True


class FAQUpdate(BaseModel):
    """Schema for updating FAQ."""
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[FAQCategory] = None
    keywords: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class FAQResponse(FAQBase):
    """Schema for FAQ response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
