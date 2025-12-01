"""
FAQ and ChatHistory models for AI module.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..database import Base


class FAQCategory(str, enum.Enum):
    """FAQ category enumeration."""
    GENERAL = "GENERAL"
    VEHICLES = "VEHICLES"
    DRIVERS = "DRIVERS"
    TRIPS = "TRIPS"
    INCIDENTS = "INCIDENTS"
    SYSTEM = "SYSTEM"
    OTHER = "OTHER"


class FAQ(Base):
    """FAQ model for chatbot knowledge base."""

    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(SQLEnum(FAQCategory), default=FAQCategory.GENERAL, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    keywords = Column(Text)  # Comma-separated keywords for search
    priority = Column(Integer, default=0)  # Higher priority FAQs shown first

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<FAQ(id={self.id}, category='{self.category}', question='{self.question[:50]}...')>"
